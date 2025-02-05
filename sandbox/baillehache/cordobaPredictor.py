from cordobaDataPreprocessor import *
import numpy
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

import torch
from torchvision import transforms as T
import cv2
# Expect a folder 'FCCDN' containing the weights and a subfolder 'networks'
# containing the FCCDN network definition
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

    def predictPcaKMeanClustering(self, images: List[CordobaImage]) -> numpy.array:
        """
        Detect difference in vegetation using two images of the same area at
        two times. Use PCA and KMeans.
        images: the two images
        Return a numpy array
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
            (clustered_image * (255 / clustered_image.max())).astype(numpy.uint8)
        return clustered_image_result

    def predictFCCDN(self, images: List[CordobaImage]) -> numpy.array:
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
