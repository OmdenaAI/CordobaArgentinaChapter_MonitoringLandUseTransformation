import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Define Vegetation Index Calculation Functions
def calculate_ndvi(image):
    nir = image[:, :, -1].astype(float)  # Simulated NIR using Red
    red = image[:, :, -2].astype(float)
    return (nir - red) / (nir + red + 1e-5)

# Load Images
before_image_path = "sandbox/before.tif"
after_image_path = "sandbox/after.tif"

before_image = np.array(Image.open(before_image_path).convert("RGB"))
after_image = np.array(Image.open(after_image_path).convert("RGB"))

# Calculate NDVI for Before and After Images
ndvi_before = calculate_ndvi(before_image)
ndvi_after = calculate_ndvi(after_image)

# Calculate NDVI Difference
ndvi_diff = ndvi_after - ndvi_before

# Prepare Features for PCA (Combine Multiple Bands/Indexes)
features_combined = np.dstack([ndvi_before, ndvi_after, ndvi_diff]).reshape(-1, 3)

# Standardize Features
scaler = StandardScaler()
features_scaled = scaler.fit_transform(features_combined)

# --- PCA Analysis ---
pca = PCA(n_components=2)
pca_features = pca.fit_transform(features_scaled)

# --- K-Means Clustering ---
kmeans = KMeans(n_clusters=3, random_state=42)
kmeans_clusters = kmeans.fit_predict(pca_features)
clustered_image = kmeans_clusters.reshape(ndvi_diff.shape)

# --- Visualization ---
plt.figure(figsize=(18, 8))

# NDVI Before
plt.subplot(2, 3, 1)
plt.title("NDVI Before")
plt.imshow(ndvi_before, cmap="RdYlGn")
plt.colorbar()

# NDVI After
plt.subplot(2, 3, 2)
plt.title("NDVI After")
plt.imshow(ndvi_after, cmap="RdYlGn")
plt.colorbar()

# NDVI Difference
plt.subplot(2, 3, 3)
plt.title("NDVI Difference")
plt.imshow(ndvi_diff, cmap="RdYlGn")
plt.colorbar()

# PCA Component 1
plt.subplot(2, 3, 4)
plt.title("PCA Component 1")
plt.imshow(pca_features[:, 0].reshape(ndvi_diff.shape), cmap="viridis")
plt.colorbar()

# PCA Component 2
plt.subplot(2, 3, 5)
plt.title("PCA Component 2")
plt.imshow(pca_features[:, 1].reshape(ndvi_diff.shape), cmap="viridis")
plt.colorbar()

# K-Means Clustering
plt.subplot(2, 3, 6)
plt.title("K-Means Clustering")
plt.imshow(clustered_image, cmap="tab10")
plt.colorbar()

plt.tight_layout()
plt.show()

# Save Results
clustered_image_result = Image.fromarray((clustered_image * (255 / clustered_image.max())).astype(np.uint8))
clustered_image_result.save("kmeans_clustered_diff.png")

print("K-Means clustered image saved as: kmeans_clustered_diff.png")
