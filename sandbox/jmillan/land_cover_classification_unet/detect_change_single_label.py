import argparse
import logging
import os
import glob
import numpy as np
from PIL import Image

def detect_forest_loss(t1_path, t2_path, output_folder):
    """Detect forest loss between t1 and t2 forest masks"""
    os.makedirs(output_folder, exist_ok=True)
    
    # Get all mask files from t1
    t1_files = glob.glob(os.path.join(t1_path, '*.png'))
    logging.info(f'Found {len(t1_files)} masks in {t1_path}')

    for t1_file in t1_files:
        # Get corresponding t2 file
        filename = os.path.basename(t1_file)
        t2_file = os.path.join(t2_path, filename)
        
        if not os.path.exists(t2_file):
            logging.warning(f"No corresponding t2 file found for {filename}")
            continue
            
        logging.info(f"\nProcessing pair: {filename}")
        
        # Read masks (they should be binary: 255 for forest, 0 for non-forest)
        t1_mask = np.array(Image.open(t1_file))
        t2_mask = np.array(Image.open(t2_file))
        
        # Convert to binary (just in case)
        t1_binary = (t1_mask > 128).astype(np.uint8)
        t2_binary = (t2_mask > 128).astype(np.uint8)
        
        # Detect forest loss: areas that were forest in t1 (1) but not in t2 (0)
        forest_loss = (t1_binary & ~t2_binary).astype(np.uint8) * 255
        
        # Save forest loss mask
        output_filename = os.path.join(output_folder, f'loss_{filename}')
        forest_loss_img = Image.fromarray(forest_loss)
        forest_loss_img.save(output_filename)
        
        # Calculate and log statistics
        total_pixels = t1_binary.size
        forest_t1 = np.sum(t1_binary)
        forest_t2 = np.sum(t2_binary)
        forest_loss_pixels = np.sum(forest_loss > 0)
        
        logging.info(f"Statistics for {filename}:")
        logging.info(f"Forest coverage t1: {forest_t1/total_pixels*100:.2f}%")
        logging.info(f"Forest coverage t2: {forest_t2/total_pixels*100:.2f}%")
        logging.info(f"Forest loss: {forest_loss_pixels/total_pixels*100:.2f}%")
        
        logging.info(f"Saved forest loss mask to {output_filename}")

def get_args():
    parser = argparse.ArgumentParser(description='Detect forest loss between t1 and t2')
    parser.add_argument('--t1', default='data/masks/t1/forest',
                        help='Folder containing t1 forest masks')
    parser.add_argument('--t2', default='data/masks/t2/forest',
                        help='Folder containing t2 forest masks')
    parser.add_argument('--output', '-o', default='data/masks/changes/forest_loss',
                        help='Folder for forest loss masks')
    return parser.parse_args()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    args = get_args()
    
    # Detect forest loss
    detect_forest_loss(
        t1_path=args.t1,
        t2_path=args.t2,
        output_folder=args.output
    )
    
    logging.info("Forest loss detection completed!") 