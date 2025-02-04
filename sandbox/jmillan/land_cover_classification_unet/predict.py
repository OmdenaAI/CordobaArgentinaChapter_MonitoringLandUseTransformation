import argparse
import logging
import os
import glob

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms

from unet import UNet
from utils.data_vis import plot_img_and_mask
from utils.dataset import BasicDataset
import matplotlib.pyplot as plt
from torch.utils.data import DataLoader


def predict_img(net,
                full_img,
                device,
                scale_factor=1,
                out_threshold=0.5):
    net.eval()

    img = torch.from_numpy(BasicDataset.preprocess(full_img, scale_factor)).float()
    #print("Input image shape:", img.shape)
    img = img.unsqueeze(0)
    img = img.to(device=device, dtype=torch.float32)

    with torch.no_grad():
        output = net(img)
        #print("Output shape:", output.shape)
        if net.n_classes > 1:
            probs = F.softmax(output, dim=1)
        else:
            probs = torch.sigmoid(output)

        probs = probs.squeeze(0)

        height, width = probs.shape[1], probs.shape[2]
        class_idx = torch.argmax(probs, dim=0)
        image = torch.zeros(height, width, 3, dtype=torch.uint8, device=device)

        mapping = {
            0: (0  , 255, 255),     #urban_land
            1: (255, 255, 0  ),     #agriculture
            2: (255, 0  , 255),     #rangeland
            3: (0  , 255, 0  ),     #forest_land
            4: (0  , 0  , 255),     #water
            5: (255, 255, 255),     #barren_land
            6: (0  , 0  , 0  )      #unknown
        }

        for k, v in mapping.items():
            idx = (class_idx == k)
            image[idx] = torch.tensor(v, dtype=torch.uint8, device=device)

        image = image.cpu()
        return image.numpy(), class_idx.cpu()

def preprocess_mask(pil_img, scale):
        w, h = pil_img.size
        newW, newH = int(scale * w), int(scale * h)
        assert newW > 0 and newH > 0, 'Scale is too small'
        pil_img = pil_img.resize((newW, newH))

        img_nd = np.array(pil_img)

        if len(img_nd.shape) == 2:
            img_nd = np.expand_dims(img_nd, axis=2)

        # HWC to CHW
        img_trans = img_nd.transpose((2, 0, 1))
        torch.set_printoptions(edgeitems=10)
        return img_trans

def predict_folder(net, input_folder, output_folder, device, scale_factor=1):
    """Predict segmentation for all images in the input folder"""
    os.makedirs(output_folder, exist_ok=True)
    
    # Get all image files from input folder
    image_files = glob.glob(os.path.join(input_folder, '*'))
    logging.info(f'Found {len(image_files)} images in {input_folder}')

    for i, fn in enumerate(image_files):
        logging.info(f"\nPredicting image {i+1}/{len(image_files)}: {fn}")

        img = Image.open(fn)
        
        # Get filename without path and extension
        filename = os.path.splitext(os.path.basename(fn))[0]
        
        # Predict
        mask, mask_indices = predict_img(net=net,
                                       full_img=img,
                                       scale_factor=scale_factor,
                                       device=device)

        # Save prediction
        output_filename = os.path.join(output_folder, f'pred_{filename}.png')
        result_img = Image.fromarray(mask)
        result_img.save(output_filename)
        
        logging.info(f"Saved prediction to {output_filename}")

def get_args():
    parser = argparse.ArgumentParser(description='Predict masks from input images')
    parser.add_argument('--model', '-m', default='MODEL.pth',
                        metavar='FILE', help="Specify the file in which the model is stored")
    parser.add_argument('--input', '-i', default='data/images/t1',
                        help='Folder containing input images')
    parser.add_argument('--output', '-o', default='predictions',
                        help='Folder for output predictions')
    parser.add_argument('--scale', '-s', type=float, default=1,
                        help='Scale factor for the input images')
    return parser.parse_args()

def RGB_2_class_idx(mask_to_be_converted):
    mapping = {(0  , 255, 255): 0,     #urban_land
                (255, 255, 0  ): 1,    #agriculture
                (255, 0  , 255): 2,    #rangeland
                (0  , 255, 0  ): 3,      #forest_land
                (0  , 0  , 255): 4,      #water
                (255, 255, 255):5,     #barren_land
                (0  , 0  , 0  ):6}           #unknown

    temp = np.array(mask_to_be_converted)
    temp = np.where(temp>=128, 255, 0)
    class_mask=torch.from_numpy(temp)
    h, w = mask_to_be_converted.shape[2], mask_to_be_converted.shape[3]
    img_no=mask_to_be_converted.shape[0]
    mask_out = torch.zeros(img_no,h, w, dtype=torch.long)

    
    for j in range (img_no):
      class_index=0
      for k in mapping:
        idx = (class_mask[j,:,:,:] == torch.tensor(k, dtype=torch.uint8).unsqueeze(1).unsqueeze(2))
        validx = (idx.sum(0) == 3)
        temp=mask_out[j,:,:]      
        temp[validx]=class_index
        mask_out[j,:,:]=temp
        class_index+=1
    
    return mask_out


def get_output_filenames(args):
    in_files = args.input
    out_files = []

    if not args.output:
        for f in in_files:
            pathsplit = os.path.splitext(f)
            out_files.append("{}_OUT{}".format(pathsplit[0], pathsplit[1]))
    elif len(in_files) != len(args.output):
        logging.error("Input files and output files are not of the same length")
        raise SystemExit()
    else:
        out_files = args.output

    return out_files


def mask_to_image(mask):
    return Image.fromarray((mask * 255).astype(np.uint8))


def compute_iou(predicted, actual, num_classes):
    iou = torch.zeros(num_classes-1, dtype=torch.float32)
    for k in range(num_classes-1):
        a = (predicted == k)
        b = (actual == k)
        intersection = torch.logical_and(a, b).sum()
        union = torch.logical_or(a, b).sum()
        iou[k] = intersection.float() / (union.float() + 1e-8)
    
    return iou.mean().item()

def get_device():
    if torch.cuda.is_available():
        return torch.device('cuda')
    elif torch.backends.mps.is_available():
        return torch.device('mps')
    return torch.device('cpu')

if __name__ == "__main__":
    args = get_args()
    
    device = get_device()
    logging.info(f'Using device {device}')
    
    # Load model
    net = UNet(n_channels=3, n_classes=7)
    logging.info(f"Loading model {args.model}")
    net.to(device=device)
    net.load_state_dict(torch.load(args.model, map_location=device))
    logging.info("Model loaded!")
    
    # Predict on all images in the folder
    predict_folder(net=net,
                  input_folder=args.input,
                  output_folder=args.output,
                  device=device,
                  scale_factor=args.scale)
    
    logging.info("Prediction completed!")
