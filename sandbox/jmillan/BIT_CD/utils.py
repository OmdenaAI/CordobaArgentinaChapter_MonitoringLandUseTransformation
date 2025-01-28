import numpy as np
import torch
from torch.utils.data import DataLoader
from torchvision import utils

import data_config
from datasets.CD_dataset import CDDataset


def get_loader(data_name, img_size=256, batch_size=8, split='test',
               is_train=False, dataset='CDDataset'):
    dataConfig = data_config.DataConfig().get_data_config(data_name)
    root_dir = dataConfig.root_dir
    label_transform = dataConfig.label_transform

    if dataset == 'CDDataset':
        data_set = CDDataset(root_dir=root_dir, split=split,
                                 img_size=img_size, is_train=is_train,
                                 label_transform=label_transform)
    else:
        raise NotImplementedError(
            'Wrong dataset name %s (choose one from [CDDataset])'
            % dataset)

    shuffle = is_train
    dataloader = DataLoader(data_set, batch_size=batch_size,
                                 shuffle=shuffle, num_workers=4)

    return dataloader


def get_loaders(args):

    data_name = args.data_name
    dataConfig = data_config.DataConfig().get_data_config(data_name)
    root_dir = dataConfig.root_dir
    label_transform = dataConfig.label_transform
    split = args.split
    split_val = 'val'
    if hasattr(args, 'split_val'):
        split_val = args.split_val
    if args.dataset == 'CDDataset':
        training_set = CDDataset(root_dir=root_dir, split=split,
                                 img_size=args.img_size,is_train=True,
                                 label_transform=label_transform)
        val_set = CDDataset(root_dir=root_dir, split=split_val,
                                 img_size=args.img_size,is_train=False,
                                 label_transform=label_transform)
    else:
        raise NotImplementedError(
            'Wrong dataset name %s (choose one from [CDDataset,])'
            % args.dataset)

    datasets = {'train': training_set, 'val': val_set}
    dataloaders = {x: DataLoader(datasets[x], batch_size=args.batch_size,
                                 shuffle=True, num_workers=args.num_workers)
                   for x in ['train', 'val']}

    return dataloaders


def make_numpy_grid(tensor_data, pad_value=0,padding=0):
    tensor_data = tensor_data.detach()
    vis = utils.make_grid(tensor_data, pad_value=pad_value,padding=padding)
    vis = np.array(vis.cpu()).transpose((1,2,0))
    if vis.shape[2] == 1:
        vis = np.stack([vis, vis, vis], axis=-1)
    return vis


def de_norm(tensor_data):
    return tensor_data * 0.5 + 0.5


def get_device(args):
    # set gpu ids
    if torch.cuda.is_available():
        torch.cuda.set_device(args.gpu_ids[0])
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")
    return device
