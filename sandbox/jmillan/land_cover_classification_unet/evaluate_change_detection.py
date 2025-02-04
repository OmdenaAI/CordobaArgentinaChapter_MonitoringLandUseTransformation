import argparse
import logging
import os
import glob
import numpy as np
from PIL import Image
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score, cohen_kappa_score

def calculate_iou(pred_mask, true_mask):
    """Calculate Intersection over Union (IoU/Jaccard Index)"""
    intersection = np.logical_and(pred_mask, true_mask).sum()
    union = np.logical_or(pred_mask, true_mask).sum()
    return intersection / union if union != 0 else 0

def evaluate_masks(pred_path, true_path):
    """Evaluate predicted forest loss masks against ground truth"""
    # Get all predicted masks
    pred_files = glob.glob(os.path.join(pred_path, '*.png'))
    logging.info(f'Found {len(pred_files)} prediction masks in {pred_path}')
    
    # Initialize metrics storage
    metrics = {
        'iou': [],
        'f1': [],
        'precision': [],
        'recall': [],
        'accuracy': [],
        'kappa': []
    }
    
    for pred_file in pred_files:
        # Get corresponding ground truth file
        filename = os.path.basename(pred_file).replace('loss_forest_pred_', '')
        true_file = os.path.join(true_path, filename)
        
        if not os.path.exists(true_file):
            logging.warning(f"No corresponding ground truth found for {filename}")
            continue
            
        logging.info(f"\nEvaluating: {filename}")
        
        # Read masks and convert to binary
        pred_size = Image.open(pred_file).size
        pred_mask = np.array(Image.open(pred_file)) > 128
        true_mask = np.array(Image.open(true_file).resize(pred_size)) > 128
        
        # Flatten masks for sklearn metrics
        pred_flat = pred_mask.ravel()
        true_flat = true_mask.ravel()
        
        # Calculate metrics
        metrics['iou'].append(calculate_iou(pred_mask, true_mask))
        metrics['f1'].append(f1_score(true_flat, pred_flat, zero_division=0))
        metrics['precision'].append(precision_score(true_flat, pred_flat, zero_division=0))
        metrics['recall'].append(recall_score(true_flat, pred_flat, zero_division=0))
        metrics['accuracy'].append(accuracy_score(true_flat, pred_flat))
        metrics['kappa'].append(cohen_kappa_score(true_flat, pred_flat))
        
        # Log individual results
        logging.info(f"Results for {filename}:")
        for metric, values in metrics.items():
            logging.info(f"{metric.upper()}: {values[-1]:.4f}")
    
    # Calculate and log average metrics
    logging.info("\nAVERAGE METRICS:")
    with open("metrics.txt", "w") as file:
        file.write("AVERAGE METRICS")
        for metric, values in metrics.items():
            mean_value = np.mean(values)
            #std_value = np.std(values)
            logging.info(f"\n{metric.upper()}: {mean_value:.4f}")
            file.write(f"\n{metric.upper()}: {mean_value:.4f}")

def get_args():
    parser = argparse.ArgumentParser(description='Evaluate forest loss detection')
    parser.add_argument('--pred', default='data/masks/changes/forest_loss',
                        help='Folder containing predicted forest loss masks')
    parser.add_argument('--true', default='data/masks/change_masks',
                        help='Folder containing ground truth change masks')
    return parser.parse_args()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    args = get_args()
    
    # Evaluate masks
    evaluate_masks(
        pred_path=args.pred,
        true_path=args.true
    )
    
    logging.info("Evaluation completed!") 