# Quick Usage Guide

## 1. Setup Environment
```bash
# Create and activate environment
conda create -n env python=3.11.8
conda activate env

# Install dependencies
pip install -r requirements.txt
```

## 2. Prepare Data
Your data should be organized as:
```
data/
  ├─A/        # Images at time t1 (RGB, 256x256)
  ├─B/        # Images at time t2 (RGB, 256x256)
  └─label/    # Ground truth masks
```

Add required prefixes to your files:
```bash
# Add prefix to files (e.g., "test_" for test set)
python add_prefix.py --folder data/A --prefix "test_"
python add_prefix.py --folder data/B --prefix "test_"
python add_prefix.py --folder data/label --prefix "test_"
```

Create the list file:
```bash
python create_list.py --path data --split test
```

## 3. Get Weights
1. Download from [Google Drive](https://drive.google.com/file/d/1IVdF5a3e1_7DiSndtMkhpZuCSgDLLFcg/view?usp=sharing)
2. Create directory: `checkpoints/name_of_project/`
3. Place downloaded model as: `checkpoints/name_of_project/best_ckpt.pt`

## 4. Update eval.sh
Change the following variables:
```bash
data_name=other
....
split=test
project_name=name_of_project
```

## 4. Run Evaluation
```bash
sh scripts/eval.sh
```

Results will be saved in:
- Predictions: `data/predictions/`
- Evaluation metrics: `checkpoints/name_of_project/`
- Visualizations: `vis/name_of_project/` 