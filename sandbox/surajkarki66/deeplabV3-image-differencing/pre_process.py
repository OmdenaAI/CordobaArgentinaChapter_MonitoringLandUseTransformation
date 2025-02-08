import cv2
import numpy as np

def preprocess_image(image_path):
    # Read image
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB

    # Resize to 512x512
    image = cv2.resize(image, (512, 512))

    # Normalize pixel values (0-1)
    image = image.astype(np.float32) / 255.0  

    # Convert (H, W, C) → (C, H, W)
    image = np.transpose(image, (2, 0, 1))

    # Add batch dimension (1, C, H, W)
    image = np.expand_dims(image, axis=0)

    return image
