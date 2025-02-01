import numpy as np
import imageio.v2 as imageio
from skimage.color import rgb2gray

from main import find_change_map

# Paths to the images
pre_change = './test_data/t1_rgb/0137.png'
post_change = './test_data/t2_rgb/0137.png'

# Load the images
pre_change_image = np.array(imageio.imread(pre_change))
post_change_image = np.array(imageio.imread(post_change))

# Convert images to grayscale
pre_change_gray = rgb2gray(pre_change_image)
post_change_gray = rgb2gray(post_change_image)

# Convert to uint8 (optional, depending on your `find_change_map` implementation)
pre_change_gray = (pre_change_gray * 255).astype(np.uint8)
post_change_gray = (post_change_gray * 255).astype(np.uint8)

# Call the function
change_map, clean_change_map = find_change_map(pre_change_gray, post_change_gray)

# Save the output images
imageio.imwrite("./results/changemap.jpg", change_map)
imageio.imwrite("./results/cleanchangemap.jpg", clean_change_map)
