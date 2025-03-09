from cordobaDataPreprocessor import *
import numpy
import pyproj
import rasterio
import geopandas as gpd

from rasterio.features import shapes, rasterize
from shapely.geometry import shape, Polygon

# from PIL import Image
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from typing import List, Tuple

# import torch
# from torchvision import transforms as T
import cv2
# Expect a folder 'FCCDN' containing the weights and a subfolder 'networks'
# containing the FCCDN network definition (cf sandbox/surajkarki66)
# from FCCDN.networks.FCCDN import FCCDN

# List of bands name in the dynamic world dataset
dynamic_world_bands = ["water", "trees", "grass", "flooded_vegetation", "crops","shrub_and_scrub", "built", "bare", "snow_and_ice"]

class CordobaPredictor:
    """
    Class implementing the deforestation detection model
    """

    def __init__(self):
        """
        Constructor for an instance of CordobaPredictor
        """
        pass

    def predict_pca_kmean_clustering(self, images: List[CordobaImage]) -> numpy.array:
        """
        Detect difference in vegetation using two images of the same area at
        two times. Use PCA and KMeans.
        images: the two images
        Return the segmented image as a 2D uint8 numpy array
        """
        # Calculate the difference of the NDVI between the two images
        ndvi_diff = images[1].bands["ndvi"] - images[0].bands["ndvi"]

        # Prepare Features for PCA (Combine Multiple Bands/Indexes)
        features_combined = \
            numpy.dstack([images[0].bands["ndvi"], images[1].bands["ndvi"], ndvi_diff]).reshape(-1, 3)

        # Standardize Features (remove meeans and scale to unit variance)
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features_combined)

        # --- PCA Analysis ---
        pca = PCA(n_components=2)
        pca_features = pca.fit_transform(features_scaled)

        # --- K-Means Clustering ---
        kmeans = KMeans(n_clusters=3, random_state=42)
        kmeans_clusters = kmeans.fit_predict(pca_features)
        clustered_image = kmeans_clusters.reshape(ndvi_diff.shape)

        # Create he result image
        clustered_image_result = \
            (clustered_image * (255.0 / clustered_image.max())).astype(numpy.uint8)
        return clustered_image_result

    # def predict_FCCDN(self, images: List[CordobaImage]) -> numpy.array:
    #     """
    #     Detect difference in vegetation using two images of the same area at
    #     two times. Use FCCD neural network.
    #     images: the two images
    #     Return the predicted mask as a numpy array (white is changed area)
    #     """

    #     # Paths and model setup
    #     pretrained_weights = "./FCCDN/FCCDN_test_LEVIR_CD.pth"

    #     # Load model
    #     model = FCCDN(num_band=3, use_se=True)
    #     pretrained_dict = torch.load(pretrained_weights, map_location="cpu", weights_only=True)
    #     module_model_state_dict = {}
    #     for item, value in pretrained_dict['model_state_dict'].items():
    #         if item[:7] == 'module.':
    #             item = item[7:]
    #         module_model_state_dict[item] = value
    #     model.load_state_dict(module_model_state_dict, strict=True)
    #     model.cpu()
    #     model.eval()

    #     # Normalization transform
    #     mean_value = [0.37772245912313807, 0.4425350597897193, 0.4464795300397427]
    #     std_value = [0.1762166286060892, 0.1917139949806914, 0.20443966020731438]
    #     normalize = T.Normalize(mean=mean_value, std=std_value)

    #     # Input images (needs to be 1024x1024 for FCCDN)
    #     pre = images[0].to_rgb()
    #     original_shape = pre.shape
    #     pre = cv2.resize(pre, (1024, 1024)) 
    #     post = images[1].to_rgb()
    #     post = cv2.resize(post, (1024, 1024)) 
        
    #     # Normalize and convert to tensor
    #     pre = normalize(torch.Tensor(pre.transpose(2, 0, 1) / 255))[None].cpu()
    #     post = normalize(torch.Tensor(post.transpose(2, 0, 1) / 255))[None].cpu()

    #     # Model prediction
    #     pred = model([pre, post])

    #     # Process outputs
    #     out = torch.round(torch.sigmoid(pred[0])).cpu().detach().numpy()
    #     out = (out[0, 0] * 255).astype(numpy.uint8)
    #     out = cv2.resize(out, [original_shape[1], original_shape[0]])
    #     return out

    def compute_Lk(self, magnitude: numpy.array, threshold: float, delta_mask: numpy.array) -> float:
        """
        Compute the success rate Lk in get_optimal_cva_threshold()
        """

        # Get the mask of magnitudes greater than the threshold
        detected_change = (magnitude >= threshold)

        # Get the number of pixels which have changed according to the threshold
        # and also according to the a-priori mask
        Ak1 = (detected_change & delta_mask).sum()

        # Get the number of pixels which have changed according to the threshold
        # and not according to the a-priori mask
        Ak2 = (detected_change & numpy.logical_not(delta_mask)).sum()

        # Get the number of pixels which have changed according to the a-priori
        # mask
        A = delta_mask.sum()

        # Compute and return the Lk value: ((Ak1 - Ak2) * 100) / A
        # Multiplied by 100 to have a percentage
        Lk = ((Ak1 - Ak2) * 100.0) / A
        return Lk

    def get_optimal_cva_threshold(self, magnitude: numpy.array, delta_classes: numpy.array, max_iteration: int=10, nb_step: int=10, epsilon: float=1e-3) -> float:
        """
        Get the optimal threshold for change detection in the CVA algorithm
        magnitude: the magnitude of change for each pixel
        delta_classes: boolean mask of change in a-priori classification, True
        means there is a priori a change
        max_iteration: maximum number of iteration to avoid infinite loop
        if no convergence
        nb_step: number of sub step during the search
        epsilon: threshold used for convergence detection
        Return the optimal threshold
        For details about the algorithm, refer to:
        https://www.researchgate.net/publication/228907009_Land-UseLand-Cover_Change_Detection_Using_Improved_Change-Vector_Analysis
        """

        # Get the minimum and maximum magnitude
        magnitude_min = numpy.min(magnitude)
        magnitude_max = numpy.max(magnitude)
        #return 0.5*(magnitude_min+magnitude_max)

        # Initialise the search range with minimum and maximum magnitude
        search_range = [magnitude_min, magnitude_max]

        # Initial best threshold and best Lk ("success rate")
        best_threshold = None
        best_Lk = None

        # Iterate until convergence or maximum number of step
        iteration = 0
        has_converged = False
        while (iteration < max_iteration) and (has_converged == False):
            iteration += 1
            print(f"search range {search_range}")
            
            # Create a list of candidate thresholds
            search_step = (search_range[1] - search_range[0]) / float(nb_step)
            candidates = numpy.arange(
                search_range[0], search_range[1] + search_step, search_step)

            # Search the best threshold among candidates (here "best" means
            # maximizing the success rate Lk)
            Lks = []
            for candidate_threshold in candidates:
                Lk = self.compute_Lk(magnitude, candidate_threshold, delta_classes)
                Lks += [Lk]
                if best_threshold is None or best_Lk < Lk:
                    best_Lk = Lk
                    best_threshold = candidate_threshold

            # Update the search range by shrinking it around the current best
            search_range[0] = best_threshold - search_step
            search_range[1] = best_threshold + search_step

            # Check the convergence condition
            has_converged = ((max(Lks) - min(Lks)) < epsilon)

        # Return the best threshold
        print(f"optimal threshold {best_threshold} for Lk {best_Lk}")
        return best_threshold
    
    def direction_cosine(self, delta_m: numpy.ndarray, delta_p: numpy.ndarray) -> float:
    
        """
        Calculate the cosine of the angle between delta_m and delta_p.
        Returns a value in [-1, 1].
        The formula is:

            cos(theta) = (delta_m . delta_p) / (||delta_m|| * ||delta_p||)

        Args:
        delta_m (numpy.ndarray): Delta vector for the model.
        delta_p (numpy.ndarray): Delta vector for the probability.

        Returns:
        float: Cosine of the angle between delta_m and delta_p. Between -1 and 1.
        """
        norm_m = numpy.linalg.norm(delta_m)
        norm_p = numpy.linalg.norm(delta_p)
        
        # To avoid division by zero
        if norm_m < 1e-12 or norm_p < 1e-12:
            return -9999 
        
        return numpy.dot(delta_m, delta_p) / (norm_m * norm_p)


    def change_type_discrimination(self, prob_t1: numpy.array, prob_t2: numpy.array, 
                                   changed_mask: numpy.array, n_classes: int) -> numpy.array:
        """
        Assign the change type (class transition) for pixels that changed.

        Args:
        prob_t1 (np.ndarray): Array (n, height, width) with probabilities at t1.
        prob_t2 (np.ndarray): Array (n, height, width) with probabilities at t2.
        changed_mask (np.ndarray): Array (height, width) boolean (True = changed).
        n_classes (int): Number of classes (e.g., 9).

        Returns:
        np.ndarray: Change map (height, width), where each "changed" pixel has a code
                    of transition a->b, and the unchanged pixels have 0.
        """
            
        # 1) Pre calculate the transition vectors
        # We use a dictionary with key=(a,b), value=delta_p_ab
        transition_vectors = {}
        
        # Generate "pure" vectors for each class
        # P_0 = (1, 0, 0, ...), P_1 = (0, 1, 0, ...) etc.
        P = numpy.eye(n_classes)
        
        for a in range(n_classes):
            for b in range(n_classes):
                if a != b:
                    delta_ab = P[b] - P[a]
                    transition_vectors[(a, b)] = delta_ab
                else:
                    transition_vectors[(a, b)] = None  # No transition (a->a)
        
        # 2) Create an empty change map
        height, width = prob_t1.shape[0], prob_t1.shape[1]
        change_map = numpy.zeros((height, width), dtype=numpy.int32)
        
        # 3) For each changed pixel, calculate Delta M and find the transition with the highest cosine
        for i in range(height):
            for j in range(width):
                if changed_mask[i, j]:
                    # Extract the probability vectors at t1 and t2
                    p1 = prob_t1[i, j, :]  # shape (n_classes, )
                    p2 = prob_t2[i, j, :]  # shape (n_classes, )
                    
                    # Delta M
                    delta_m = p2 - p1
                    
                    # Search for the transition (a->b) with the highest cosine
                    best_cos = -9999
                    best_transition = (0, 0)
                    
                    for (a, b), delta_ab in transition_vectors.items():
                        if delta_ab is None:
                            continue
                        cos_val = self.direction_cosine(delta_m, delta_ab)
                        if cos_val > best_cos:
                            best_cos = cos_val
                            best_transition = (a, b)
                    
                    # Code the transition a->b as a number, e.g. a * 100 + b
                    a, b = best_transition
                    transition_code = a * 100 + b
                    
                    change_map[i, j] = transition_code
                else:
                    # Unchanged pixel
                    change_map[i, j] = 0 
        
        return change_map


    def predict_CVA(self, images: List[CordobaImage]) -> numpy.array:
        """
        Detect change using two images of the same area at two different times
        using Change Vector Analysis.
        images: the two satellite images
        
        Return a boolean numpy array, the mask of pixels which were
        classified as target_class in the first image and as something else
        in the second image.
        """
        
        # Get the masks for the target class at T1 and T2
        target_T1 = images[0].to_dynamic_world_mask()
        target_T2 = images[1].to_dynamic_world_mask()

        # Get the mask of difference between the target class at T1 and T2
        mask_delta_target = (target_T1 != target_T2).astype(numpy.uint8)

        # Get the bands data of satellite images at T1 and T2
        bands_T1 = images[0].get_bands_as_vectors()
        bands_T2 = images[1].get_bands_as_vectors()

        # Get the delta of bands data between T1 and T2
        delta_bands = bands_T2 - bands_T1

        # Get the magnitude of change in bands using euclidean distance
        magnitude = numpy.linalg.norm(delta_bands, axis=2)
        #Image.fromarray((magnitude/magnitude.max()*255.0).astype(numpy.uint8)).save("/tmp/magnitude_trees.png")

        # Get the optimal threshold value
        threshold_change = \
            self.get_optimal_cva_threshold(magnitude, mask_delta_target)
        
        change_mask_magnitude = (magnitude >= threshold_change)

        change_map = self.change_type_discrimination(bands_T1, bands_T2, change_mask_magnitude, 9)

        forest_change = ((change_map >= 100) & (change_map <= 199)).astype(numpy.uint8) 

        return forest_change

        # # Create the change mask according to the magnitude of bands change
        # # and the optimal threshold
        # change_mask_magnitude = (magnitude >= threshold_change)
        # return change_mask_magnitude

        # Create the final change mask by discriminating between classes
        # changes based on magnitude
        # TODO

    def predict_dynamic_world(self, images: List[CordobaImage], target_class: str, 
                              threshold_mask=0.0) -> numpy.array:
        """
        Detect change using two images of the same area at two different times
        using dynamic world classification.
        images: the two dynamic world classification images
        target_class: the class in dynamic world classes for which we search
        change
        threshold_mask: minimum probabilities (level of confidence) needed to
        assume a pixel is really in the class DW tells us it is
        Return the mask as a boolean numpy array, the mask of pixels which were
        classified as target_class in the first image and as something else
        in the second image.
        """
        
        # Get the masks for the target class at T1 and T2
        target_T1 = images[0].to_dynamic_world_mask(target_class, threshold_mask)
        target_T2 = images[1].to_dynamic_world_mask(target_class, 0.0)

        # Get the mask of areas containing the target class at T1 but not at T2
        mask_delta_target = (target_T1 & numpy.logical_not(target_T2))
        return mask_delta_target


    def create_area_mask(self, shape: Tuple[int, int], area_of_interest: ee.Geometry.Polygon) -> numpy.ndarray:
        """
        Create a binary mask from the area of interest coordinates.
        shape: the shape of the mask (height, width)
        area_of_interest: the area of interest as an ee.Geometry.Polygon
        resolution: the resolution of the mask in meters
        Return the binary mask
        """
        # Convert the coordinates of the area of interest to UTM
        coords = area_of_interest.coordinates().getInfo()[0]
        lat_from, lon_from, lat_to, lon_to = coords[0][1], coords[0][0], coords[2][1], coords[2][0]
        utm_code = query_utm_crs_info(datum_name='WGS 84', area_of_interest=AreaOfInterest(lon_from, lat_from, lon_to, lat_to))
        utm_zone = utm_code[0].code
        
        # Convert the coordinates to UTM
        utm_transformer = pyproj.Transformer.from_crs('epsg:4326', f"epsg:{utm_zone}", always_xy=True)
        utm_coords = [utm_transformer.transform(lon, lat) for lon, lat in coords]

        # Convert to shapely polygon
        polygon = Polygon(utm_coords)

        # Create a transformation of coordinates
        x_min, y_min, x_max, y_max = polygon.bounds
        transform = rasterio.transform.from_bounds(x_min, y_min, x_max, y_max, shape[1], shape[0])

        # Rasterize the polygon
        mask = rasterize([polygon], out_shape=shape, transform=transform, all_touched=True, fill=0, 
                                           default_value=1, dtype=numpy.uint8)

        return mask, utm_zone

    def convert_mask_to_polygon(self, mask: numpy.ndarray, area_of_interest: LongLatBBox) -> List[List[Tuple[float, float]]]:
        """
        Convert a mask to a list of polygons.
        mask: the mask to convert
        area_of_interest: the area of interest as a LongLatBBox
        resolution: the resolution of the mask in meters
        Return the list of polygons
        """
        # Create a binary mask from the area of interest coordinates
        area_mask, crs = self.create_area_mask(mask.shape, area_of_interest.to_ee_polygon())
        
        # Apply the area mask to the input mask
        mask = mask * area_mask
        
        # Vectorize the result
        transform = rasterio.transform.from_bounds(area_of_interest.long_from, area_of_interest.lat_from, area_of_interest.long_to, area_of_interest.lat_to, mask.shape[1], mask.shape[0])
        shapes_gen = shapes(mask, transform=transform)
        vectors = [(shape(s), v) for s, v in shapes_gen if v == 1]

        # Convert shapes to polygons
        polygons = [s for s, _ in vectors]

        # Convert as a GeoJSON format
        gdf = gpd.GeoDataFrame(geometry=polygons, crs=f"EPSG:{crs}")

        return gdf

