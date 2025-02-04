import argparse
import logging
import os
import glob
import numpy as np
from PIL import Image

def extract_forest_mask(input_mask_path, output_folder):
    """Extract forest class (index 3) from prediction masks"""
    os.makedirs(output_folder, exist_ok=True)
    
    # Get all mask files
    mask_files = glob.glob(os.path.join(input_mask_path, '*'))
    logging.info(f'Found {len(mask_files)} masks in {input_mask_path}')

    # RGB values for different classes
    forest_rgb = np.array([0, 255, 0])  # Green color for forest
    
    for i, fn in enumerate(mask_files):
        logging.info(f"\nProcessing mask {i+1}/{len(mask_files)}: {fn}")
        
        # Read mask
        mask = np.array(Image.open(fn))
        
        # Create binary mask where forest pixels are 255 and others are 0
        forest_mask = np.all(mask == forest_rgb, axis=-1).astype(np.uint8) * 255
        
        # Save binary forest mask
        filename = os.path.splitext(os.path.basename(fn))[0]
        output_filename = os.path.join(output_folder, f'forest_{filename}.png')
        
        # Save as binary image
        forest_img = Image.fromarray(forest_mask)
        forest_img.save(output_filename)
        
        logging.info(f"Saved forest mask to {output_filename}")

def get_args():
    parser = argparse.ArgumentParser(description='Extract forest masks from prediction masks')
    parser.add_argument('--input', '-i', default='data/masks/t1',
                        help='Folder containing prediction masks')
    parser.add_argument('--output', '-o', default='data/masks/t1/forest',
                        help='Folder for forest masks output')
    return parser.parse_args()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    args = get_args()
    
    # Extract forest masks
    extract_forest_mask(
        input_mask_path=args.input,
        output_folder=args.output
    )
    
    logging.info("Forest mask extraction completed!") 