import os
import torch

from torchvision import transforms as T

import cv2
import numpy as np

from networks.FCCDN import FCCDN

# Paths and model setup
test_out_path = "./results/"
pretrained_weights = "./pretrained/FCCDN_test_LEVIR_CD.pth"
mean_value = [0.37772245912313807, 0.4425350597897193, 0.4464795300397427]
std_value = [0.1762166286060892, 0.1917139949806914, 0.20443966020731438]

# Ensure output directories exist
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

# Inference
with torch.no_grad():
    # Load input images
    pre = cv2.imread(os.path.join("data", "pre.png"))
    post = cv2.imread(os.path.join("data", "post.png"))

    # Normalize and convert to tensor
    pre = normalize(torch.Tensor(pre.transpose(2, 0, 1) / 255))[None].cpu()
    post = normalize(torch.Tensor(post.transpose(2, 0, 1) / 255))[None].cpu()

    # Model prediction
    pred = model([pre, post])

    # Process outputs
    out = torch.round(torch.sigmoid(pred[0])).cpu().numpy()
    
    # Save results with proper extensions
    cv2.imwrite(os.path.join(test_out_path, "change.png"), (out[0, 0] * 255).astype(np.uint8))