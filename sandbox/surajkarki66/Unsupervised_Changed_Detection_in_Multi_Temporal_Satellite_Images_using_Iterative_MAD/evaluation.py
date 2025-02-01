import os
import json
import numpy as np
import imageio.v2 as imageio

from sklearn.metrics import (
    jaccard_score, f1_score, precision_score, recall_score, accuracy_score, cohen_kappa_score
)

from main import IRMAD, get_binary_change_map

# Paths and model setup
base_path = './test_data'
t1_path = os.path.join(base_path, 't1_rgb')
t2_path = os.path.join(base_path, 't2_rgb')
gt_path = os.path.join(base_path, 'gt_grayscale')
test_out_path = "./results/"
metrics_out_file = os.path.join(test_out_path, "metrics_results.json")

# Ensure output directory exists
os.makedirs(test_out_path, exist_ok=True)

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
all_metrics = {}

for filename in os.listdir(t1_path):
    t1_image_path = os.path.join(t1_path, filename)
    t2_image_path = os.path.join(t2_path, filename)
    gt_image_path = os.path.join(gt_path, filename)

    # Check if corresponding files exist
    if not os.path.isfile(t2_image_path) or not os.path.isfile(gt_image_path):
        print(f"Missing corresponding file for {filename}")
        continue

    # Load input images and ground truth
    pre = np.array(imageio.imread(t1_image_path))
    post = np.array(imageio.imread(t2_image_path))
    ground_truth = np.array(imageio.imread(gt_image_path))

    img_height, img_width, _ = pre.shape
   
    img_X = np.reshape(pre, (-1, img_height, img_width))
    img_Y = np.reshape(post, (-1, img_height, img_width))

    channel, img_height, img_width = img_X.shape


    img_X = np.reshape(img_X, (channel, -1))
    img_Y = np.reshape(img_Y, (channel, -1))
    
    # when max_iter is set to 1, IRMAD becomes MAD
    mad, can_coo, mad_var, ev_1, ev_2, sigma_11, sigma_22, sigma_12, chi2, noc_weight = IRMAD(img_X, img_Y,
                                                                                              max_iter=10,
                                                                                              epsilon=1e-3)
    sqrt_chi2 = np.sqrt(chi2)

    k_means_bcm = get_binary_change_map(sqrt_chi2)
    k_means_bcm = np.reshape(k_means_bcm, (img_height, img_width)).astype(np.uint8)
 
    # Save the output change map for visualization
    imageio.imwrite(os.path.join(test_out_path, f"{filename}_change.png"), k_means_bcm)

    # Evaluate metrics
    metrics = evaluate_metrics(k_means_bcm, ground_truth)
    print(f"Metrics for {filename}: {metrics}")

    # Save metrics for this image
    all_metrics[filename] = metrics

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

    # Save metrics to JSON
    all_metrics["Average"] = avg_metrics
    with open(metrics_out_file, "w") as f:
        json.dump(all_metrics, f, indent=4)
    print(f"Metrics saved to {metrics_out_file}")
else:
    print("No images processed.")
