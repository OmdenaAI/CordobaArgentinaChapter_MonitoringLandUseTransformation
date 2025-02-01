import os
import rasterio
import numpy as np
import cv2

# Input and output folder paths
input_folder = "./test_data/gt"
output_folder = "./test_data/"

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)

# Loop through all .tif files in the input folder
for file_name in os.listdir(input_folder):
    if file_name.endswith(".tif"):
        file_path = os.path.join(input_folder, file_name)

        # Open the .tif file and read the first band
        with rasterio.open(file_path) as src:
            band1 = src.read(1)  # First band (assumed as grayscale)
            print(band1)

        # Normalize the band to 0-255
        band1_normalized = np.interp(band1, (band1.min(), band1.max()), (0, 255)).astype(np.uint8)

        # Define output file path
        output_file_path = os.path.join(output_folder, file_name.replace(".tif", ".png"))

        # Save the grayscale image
        cv2.imwrite(output_file_path, band1_normalized)

        print(f"Saved Grayscale image: {output_file_path}")

print("All images have been processed and saved as grayscale!")
