from cordobaDataPreprocessor import *
import numpy
from PIL import Image
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

import torch
from torchvision import transforms as T
import cv2
# Expect a folder 'FCCDN' containing the weights and a subfolder 'networks'
# containing the FCCDN network definition (cf sandbox/surajkarki66)
from FCCDN.networks.FCCDN import FCCDN

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

    def predict_FCCDN(self, images: List[CordobaImage]) -> numpy.array:
        """
        Detect difference in vegetation using two images of the same area at
        two times. Use FCCD neural network.
        images: the two images
        Return the predicted mask as a numpy array (white is changed area)
        """

        # Paths and model setup
        pretrained_weights = "./FCCDN/FCCDN_test_LEVIR_CD.pth"

        # Load model
        model = FCCDN(num_band=3, use_se=True)
        pretrained_dict = torch.load(pretrained_weights, map_location="cpu", weights_only=True)
        module_model_state_dict = {}
        for item, value in pretrained_dict['model_state_dict'].items():
            if item[:7] == 'module.':
                item = item[7:]
            module_model_state_dict[item] = value
        model.load_state_dict(module_model_state_dict, strict=True)
        model.cpu()
        model.eval()

        # Normalization transform
        mean_value = [0.37772245912313807, 0.4425350597897193, 0.4464795300397427]
        std_value = [0.1762166286060892, 0.1917139949806914, 0.20443966020731438]
        normalize = T.Normalize(mean=mean_value, std=std_value)

        # Input images (needs to be 1024x1024 for FCCDN)
        pre = images[0].to_rgb()
        original_shape = pre.shape
        pre = cv2.resize(pre, (1024, 1024)) 
        post = images[1].to_rgb()
        post = cv2.resize(post, (1024, 1024)) 
        
        # Normalize and convert to tensor
        pre = normalize(torch.Tensor(pre.transpose(2, 0, 1) / 255))[None].cpu()
        post = normalize(torch.Tensor(post.transpose(2, 0, 1) / 255))[None].cpu()

        # Model prediction
        pred = model([pre, post])

        # Process outputs
        out = torch.round(torch.sigmoid(pred[0])).cpu().detach().numpy()
        out = (out[0, 0] * 255).astype(numpy.uint8)
        out = cv2.resize(out, [original_shape[1], original_shape[0]])
        return out

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

    def predict_CVA(self, images: List[CordobaImage], lbl_bands: List[str], target_class: str, threshold_mask=0.0) -> numpy.array:
        """
        Detect change using two images of the same area at two different times
        using Change Vector Analysis.
        images: the two satellite images
        lbl_bands: bands in satellite image to use for detection
        target_class: the class in dynamic world classes for which we do the
        analysis
        threshold_mask: minimum probabilities (level of confidence) needed to
        assume a pixel is really in the class DW tells us it is
        Return a boolean numpy array, the mask of pixels which were
        classified as target_class in the first image and as something else
        in the second image.
        """
        
        # Get the masks for the target class at T1 and T2
        target_T1 = images[0].to_dynamic_world_mask(target_class, threshold_mask)
        target_T2 = images[1].to_dynamic_world_mask(target_class, 0.0)

        # Get the mask of difference between the target class at T1 and T2
        mask_delta_target = (target_T1 & numpy.logical_not(target_T2))

        # Get the bands data of satellite images at T1 and T2
        bands_T1 = images[0].get_bands_as_vectors(lbl_bands)
        bands_T2 = images[1].get_bands_as_vectors(lbl_bands)

        # Get the delta of bands data between T1 and T2
        delta_bands = bands_T2 - bands_T1

        # Get the magnitude of change in bands using euclidean distance
        magnitude = numpy.linalg.norm(delta_bands, axis=2)
        #Image.fromarray((magnitude/magnitude.max()*255.0).astype(numpy.uint8)).save("/tmp/magnitude_trees.png")

        # Get the optimal threshold value
        threshold_change = \
            self.get_optimal_cva_threshold(magnitude, mask_delta_target)
        
        # Create the change mask according to the magnitude of bands change
        # and the optimal threshold
        change_mask_magnitude = (magnitude >= threshold_change)
        return change_mask_magnitude

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
        target_T2 = images[1].to_dynamic_world_mask(target_class, 0.0)

        # Get the mask of areas containing the target class at T1 but not at T2
        mask_delta_target = (target_T1 & numpy.logical_not(target_T2))
        return mask_delta_target
