import os
from PIL import Image

# Path to the folder containing the images
folder_path = './test_data/gt_grayscale'

# Target size for resizing
target_size = (506, 506)

# Iterate over all files in the folder
for filename in os.listdir(folder_path):
    file_path = os.path.join(folder_path, filename)

    # Check if the file is an image (optional: filter by extensions)
    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.bmp')):
        try:
            # Open the image
            with Image.open(file_path) as img:
                # Ensure the image is grayscale
                if img.mode != 'L':
                    img = img.convert('L')

                # Resize the image
                resized_img = img.resize(target_size, Image.BICUBIC)

                # Save the resized image, replacing the original
                resized_img.save(file_path)

                print(f"Resized and replaced: {filename}")

        except Exception as e:
            print(f"Error processing {filename}: {e}")

print("All images have been resized!")
