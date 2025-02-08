import numpy as np
import cv2
import matplotlib.pyplot as plt
import onnxruntime as ort

from pre_process import preprocess_image

# Load the ONNX model
model_path = "./models/deeplabv3_landcover_4c.onnx"
ort_session = ort.InferenceSession(model_path)

# Get model input name
input_name = ort_session.get_inputs()[0].name

def run_segmentation(image_path):
    """ Preprocess image, run inference, and return segmentation mask """
    image = preprocess_image(image_path)  # Preprocess input
    outputs = ort_session.run(None, {input_name: image})  # Run inference
    output_mask = outputs[0]  # Shape: (1, 4, 512, 512)
    
    # Convert probabilities to class index (highest probability per pixel)
    segmentation_map = np.argmax(output_mask, axis=1).squeeze()  # Shape: (512, 512)

    return segmentation_map

def create_binary_mask(segmentation_map):
    """ Create a binary mask where woodland (2) is 1, others are 0 """
    binary_mask = np.zeros_like(segmentation_map, dtype=np.uint8)
    binary_mask[segmentation_map == 2] = 1  # Woodland → 1, others → 0
    
    return binary_mask

def create_forest_change_mask(pre_mask, post_mask):
    """Create a mask where:
       - -1 (loss) is replaced by green
       - 1 (gain) is replaced by red
       - 0 (no change) is replaced by black
    """
    # Compute the difference: pre_mask - post_mask
    change_mask = pre_mask.astype(np.int16) - post_mask.astype(np.int16)

    # Initialize an empty image (height, width, 3 channels for RGB)
    height, width = change_mask.shape
    color_mask = np.zeros((height, width, 3), dtype=np.uint8)

    # Replace -1 (loss) with green [0, 255, 0]
    color_mask[change_mask == -1] = [0, 255, 0]  # Green

    # Replace +1 (gain) with red [255, 0, 0]
    color_mask[change_mask == 1] = [255, 0, 0]  # Red

    # Replace 0 (no change) with black [0, 0, 0]
    color_mask[change_mask == 0] = [0, 0, 0]  # Black

    return color_mask

# Process both images
pre_segmentation = run_segmentation("./images/image.jpg")
post_segmentation = run_segmentation("./images/image(1).jpg")

# Generate binary woodland masks (0 and 1 only)
pre_woodland_mask = create_binary_mask(pre_segmentation)
post_woodland_mask = create_binary_mask(post_segmentation)

# Compute forest change mask
forest_change_mask = create_forest_change_mask(pre_woodland_mask, post_woodland_mask)

# Display the original images, binary masks, and change mask in a single subplot
fig, ax = plt.subplots(2, 4, figsize=(20, 10))

# Original Pre Image
ax[0, 0].imshow(cv2.cvtColor(cv2.imread("./images/image.jpg"), cv2.COLOR_BGR2RGB))  # Convert BGR to RGB
ax[0, 0].set_title("Original Pre Image")
ax[0, 0].axis("off")

# Binary Woodland Mask for Pre Image
ax[0, 1].imshow(pre_woodland_mask * 255, cmap="gray")  # Convert 0/1 to grayscale (0-255)
ax[0, 1].set_title("Pre Image Mask ( black = Non-Woodland, white = Woodland)")
ax[0, 1].axis("off")

# Original Post Image
ax[0, 2].imshow(cv2.cvtColor(cv2.imread("./images/image(1).jpg"), cv2.COLOR_BGR2RGB))  # Convert BGR to RGB
ax[0, 2].set_title("Original Post Image")
ax[0, 2].axis("off")

# Binary Woodland Mask for Post Image
ax[0, 3].imshow(post_woodland_mask * 255, cmap="gray")  # Convert 0/1 to grayscale (0-255)
ax[0, 3].set_title("Post Image Mask ( black = Non-Woodland, white = Woodland)")
ax[0, 3].axis("off")

# Forest Change Mask
ax[1, 0].imshow(forest_change_mask)
ax[1, 0].set_title("Change Mask (Red = Lost Woodland, Green = Woodland)")
ax[1, 0].axis("off")

# Additional empty subplot for spacing
ax[1, 1].axis("off")

# Additional empty subplot for spacing
ax[1, 2].axis("off")

# Additional empty subplot for spacing
ax[1, 3].axis("off")

plt.tight_layout()
plt.savefig("forest_change_visualization.png")

plt.show()
