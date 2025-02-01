import os
import rasterio
import numpy as np
import cv2

# Input and output folder paths
input_folder = "./test_data/t2"
output_folder = "./test_data/"

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)

# Loop through all .tif files in the input folder
for file_name in os.listdir(input_folder):
    if file_name.endswith(".tif"):
        file_path = os.path.join(input_folder, file_name)

        # Open the .tif file and read the bands
        with rasterio.open(file_path) as src:
            band3 = src.read(3)  # Red
            band2 = src.read(2)  # Green
            band1 = src.read(1)  # Blue

        # Normalize each band to 0-255
        band3 = np.interp(band3, (band3.min(), band3.max()), (0, 255)).astype(np.uint8)
        band2 = np.interp(band2, (band2.min(), band2.max()), (0, 255)).astype(np.uint8)
        band1 = np.interp(band1, (band1.min(), band1.max()), (0, 255)).astype(np.uint8)

        # Stack the bands into an RGB image
        rgb_image = np.dstack((band3, band2, band1))

        # Define output file path
        output_file_path = os.path.join(output_folder, file_name.replace(".tif", ".png"))

        # Save the image
        cv2.imwrite(output_file_path, cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR))

        print(f"Saved RGB image: {output_file_path}")

print("All images have been processed and saved!")
