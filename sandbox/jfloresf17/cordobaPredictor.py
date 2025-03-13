from cordobaDataPreprocessor import *
import numpy
import cv2
import pyproj
import rasterio

from skimage.morphology import remove_small_objects
from typing import List, Dict
from shapely.geometry import Polygon
from rasterio.features import rasterize
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


class CordobaPredictor:
    """
    Class implementing the deforestation detection model
    """

    def __init__(self):
        """
        Constructor for an instance of CordobaPredictor
        """
        pass

    def get_ee_geometry_from_mask(self, image: CordobaImage, mask: numpy.array, aoi: ee.Geometry=None) -> List[ee.Geometry]:
        """
        Convert a boolean mask into a list of ee.Geometry surrounding the 'True'
        areas. The contours will only include polygons inside the ROI.
        
        image: the CordobaImage associated with the mask (for coordinate
        conversion)
        mask: the mask to be converted
        aoi: the area of interest (optional) to clip the result
        Create and return `ee.Geometry` objects from the contours in the mask.
        """
        if aoi is not None:
            # Get the shape of the mask
            height, width = mask.shape
            bbox = [image.area.long_from, image.area.lat_from, image.area.long_to, image.area.lat_to]

            # Get the ROI polygon
            roi_polygon = Polygon(aoi.getInfo()["coordinates"][0])
            transform = rasterio.transform.from_bounds(*bbox, width, height)

            roi_mask = rasterize(
                        [roi_polygon],
                        out_shape=(height, width),
                        transform=transform,
                        all_touched=True,
                        fill=0,
                        default_value=1,
                        dtype=numpy.uint8
                    )

            clipped_mask = mask & roi_mask

            contours, _ = cv2.findContours( 
                clipped_mask.astype(numpy.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        else:
            contours, _ = cv2.findContours(
                mask.astype(numpy.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        
        # Loop through the contours to create geometries
        geometries = []
        for contour in contours:
            coords = []
            for node in contour:
                # Convert the coordinates from pixel to longitude/latitude
                lon = (float(node[0][0]) / float(image.width)) * (image.area.long_to - image.area.long_from) + image.area.long_from
                lat = image.area.lat_to - (float(node[0][1]) / float(image.height)) * (image.area.lat_to - image.area.lat_from)
                coords.append([lon, lat])

            # If the contour has at least three nodes, check if it is within the ROI
            if len(coords) > 2:
                contour_geometry = ee.Geometry.Polygon([coords])
                geometries.append(contour_geometry)

                if aoi is None or roi_polygon.intersects(Polygon(coords)):
                    geometries.append(contour_geometry)

        # Return the list of geometries that are inside the ROI
        return geometries
    
    def get_contours_from_mask(self, image: CordobaImage, mask: numpy.array, gamma=1.0) -> numpy.array:
        """
        Convert a boolean mask into an image of the contours surrounding the
        'True' areas.
        image: the CordobaImage associated with the mask (for coordinate
        conversion)
        mask: the mask to be converted
        gamma: gamma correction
        Create and return the image as a numpy array.
        """
        # Find the contours in the mask
        contours, _ = cv2.findContours(
            mask.astype(numpy.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        # Get the RGB image
        rgb = image.to_rgb(gamma)
        # Draw the contours on the RGB image
        cv2.drawContours(rgb, contours, -1, (255,255,255), 1)
        # Return the annotated image
        return rgb

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
        if A == 0:
            return 0  # Avoid division by zero
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
        TODO:
        The DFPS algorithm is not intended to be used on a single image but rather on a dataset of change/no-change pixels, with change pixels identified in a prior step and no-change pixels limited to a small surrounding window around change pixels.
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

    def predict_CVA(self, images: List[CordobaImage], target_class: str, 
                    threshold_change: Dict[str, float], threshold_mask=0.0) -> numpy.array:
        """
        Detect change using two images of the same area at two different times
        using Change Vector Analysis (CVA).

        images: List of two CordobaImage objects (T1 and T2).
        target_class: The target class for classification in Dynamic World.
        threshold_change: Dictionary with band names as keys and threshold changes as values.
        threshold_mask: Minimum probability required to assume a pixel belongs to target_class.

        Returns:
            Boolean numpy array (change mask), identifying pixels that changed.
        """
        
        # Obtain initial change mask from Dynamic World
        mask_delta_target = self.predict_dynamic_world(images, target_class, threshold_mask)

        tree_T1 = list(images[0].classes.values())[1]
        tree_T2 = list(images[1].classes.values())[1]

        # Calculate band differences (delta)
        delta_bands = tree_T2 - tree_T1  # Shape: (num_bands, height, width)

        # Compute Euclidean magnitude of change
        magnitude = numpy.linalg.norm(delta_bands[None], axis=0)  # Shape: (height, width)

        # Determine optimal threshold for change detection
        optimal_threshold_change = self.get_optimal_cva_threshold(magnitude, mask_delta_target)

        # Create initial change mask based on magnitude threshold
        change_mask_magnitude = (magnitude >= optimal_threshold_change)

        num_votes = len(threshold_change) // 2
        bands = []
        for band, threshold in threshold_change.items():
            bands_T1 = images[0].get_bands_as_vectors([band])
            bands_T2 = images[1].get_bands_as_vectors([band])

            diff_bands = bands_T2 - bands_T1
            change_mask_band = (diff_bands <= threshold)
            change_mask_band = numpy.squeeze(change_mask_band, axis=-1)
            bands.append(change_mask_band)

        ## Add the change mask to diff_bands
        stacked_bands = numpy.stack(bands, axis=0)
        stacked_diff_bands = numpy.concatenate((change_mask_magnitude[None], stacked_bands), axis=0)

        ## Apply majority voting
        change_mask = (numpy.sum(stacked_diff_bands, axis=0) >= num_votes).astype(numpy.uint8)

        # Erode and dilate operations
        kernel = numpy.ones((3, 3), numpy.uint8)
        dilated_mask = cv2.dilate(change_mask, kernel, iterations=1)
        eroded_mask = cv2.erode(dilated_mask.astype(numpy.uint8), kernel, iterations=1)


        # Apply remove small objects using skimage
        clean_change_mask = remove_small_objects(eroded_mask.astype(bool), min_size=16, connectivity=1)

        return clean_change_mask

        # Create the final change mask by discriminating between classes
        # changes based on magnitude
        # TODO

    def predict_dynamic_world(self, images: List[CordobaImage], target_class: str, threshold_mask=0.0) -> numpy.array:
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
        target_T2 = images[1].to_dynamic_world_mask(target_class, threshold_mask)

        # Get the mask of areas containing the target class at T1 but not at T2
        mask_delta_target = (target_T1 & numpy.logical_not(target_T2))
        return mask_delta_target
