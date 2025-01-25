import os
import torch
import cv2
import numpy as np
import imageio.v2 as imageio

from torchvision import transforms as T
from sklearn.metrics import (
    jaccard_score, f1_score, precision_score, recall_score, accuracy_score, cohen_kappa_score
)
from networks.FCCDN import FCCDN

# Paths and model setup
base_path = './test_data'
t1_path = os.path.join(base_path, 't1')
t2_path = os.path.join(base_path, 't2')
gt_path = os.path.join(base_path, 'gt')
test_out_path = "./results/"
pretrained_weights = "./pretrained/FCCDN_test_LEVIR_CD.pth"
mean_value = [0.37772245912313807, 0.4425350597897193, 0.4464795300397427]
std_value = [0.1762166286060892, 0.1917139949806914, 0.20443966020731438]

# Ensure output directory exists
os.makedirs(test_out_path, exist_ok=True)

# Load model
model = FCCDN(num_band=3, use_se=True)
pretrained_dict = torch.load(pretrained_weights, map_location="cpu")
module_model_state_dict = {}
for item, value in pretrained_dict['model_state_dict'].items():
    if item[:7] == 'module.':
        item = item[7:]
    module_model_state_dict[item] = value
model.load_state_dict(module_model_state_dict, strict=True)
model.cpu()
model.eval()

# Normalization transform
normalize = T.Normalize(mean=mean_value, std=std_value)

# Evaluation metrics function
def evaluate_metrics(predicted, ground_truth):
    # Flatten both arrays
    predicted = predicted.flatten()
    ground_truth = ground_truth.flatten()

    # Normalize to binary labels if necessary (0 and 1)
    if 255 in predicted or 255 in ground_truth:
        predicted = (predicted / 255).astype(int)
        ground_truth = (ground_truth / 255).astype(int)
    
    # Calculate metrics
    metrics = {
        "Jaccard Index (IoU)": jaccard_score(ground_truth, predicted, average="binary"),
        "F1 Score": f1_score(ground_truth, predicted, average="binary"),
        "Precision": precision_score(ground_truth, predicted, average="binary"),
        "Recall": recall_score(ground_truth, predicted, average="binary"),
        "Accuracy": accuracy_score(ground_truth, predicted),
        "Cohen's Kappa Score": cohen_kappa_score(ground_truth, predicted)
    }
    return metrics

# Initialize variables to track the sum of each metric
metric_sums = {
    "Jaccard Index (IoU)": 0,
    "F1 Score": 0,
    "Precision": 0,
    "Recall": 0,
    "Accuracy": 0,
    "Cohen's Kappa Score": 0
}

# Total number of images processed
num_images = 0

# Inference and evaluation loop
with torch.no_grad():
    for filename in os.listdir(t1_path):
        t1_image_path = os.path.join(t1_path, filename)
        t2_image_path = os.path.join(t2_path, filename)
        gt_image_path = os.path.join(gt_path, filename)

        # Check if corresponding files exist
        if not os.path.isfile(t2_image_path) or not os.path.isfile(gt_image_path):
            print(f"Missing corresponding file for {filename}")
            continue

        # Load input images and ground truth
        pre = cv2.imread(t1_image_path)
        post = cv2.imread(t2_image_path)
        ground_truth = np.array(imageio.imread(gt_image_path))

        # Normalize and convert to tensor
        pre = normalize(torch.Tensor(pre.transpose(2, 0, 1) / 255))[None].cpu()
        post = normalize(torch.Tensor(post.transpose(2, 0, 1) / 255))[None].cpu()

        # Model prediction
        pred = model([pre, post])
        change_mask = torch.round(torch.sigmoid(pred[0])).cpu().numpy()[0, 0]

        # Post-process change mask (convert to binary 0/255)
        change_mask = (change_mask * 255).astype(np.uint8)

        # Save the output change map for visualization
        cv2.imwrite(os.path.join(test_out_path, f"{filename}_change.png"), change_mask)

        # Evaluate metrics
        metrics = evaluate_metrics(change_mask, ground_truth)
        print(f"Metrics for {filename}: {metrics}")

        # Add metrics to the sums
        for metric_name in metrics:
            metric_sums[metric_name] += metrics[metric_name]
        
        num_images += 1

# Calculate the average of each metric
if num_images > 0:
    avg_metrics = {metric: metric_sums[metric] / num_images for metric in metric_sums}
    print("\nAverage Metrics:")
    for metric, avg_value in avg_metrics.items():
        print(f"{metric}: {avg_value:.4f}")
else:
    print("No images processed.")
