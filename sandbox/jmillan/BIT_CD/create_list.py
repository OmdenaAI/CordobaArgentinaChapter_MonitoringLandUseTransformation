import os
from pathlib import Path
import argparse

def create_list(path, split):
    """Create a list file for change detection dataset.
    
    Args:
        path (str): Path to data directory containing A, B, and label folders
        split (str): One of 'train', 'test', or 'val'
    """
    # Path to data folder and label folder
    data_dir = Path(path)
    label_dir = data_dir / "label"
    
    if not label_dir.exists():
        raise FileNotFoundError(f"Directory not found at {label_dir}")
    
    # Get all files from label directory
    image_list = []
    for img_path in sorted(label_dir.glob("*")):
        # Get filename without extension
        base_name = img_path.stem + ".png"
        image_list.append(base_name)
    
    # Create list directory if it doesn't exist
    list_dir = data_dir / "list"
    list_dir.mkdir(exist_ok=True)
    
    # Write the list file
    with open(list_dir / f"{split}.txt", "w") as f:
        for name in image_list:
            if name.split("_")[0] == split:
                f.write(f"{name}\n")
    
    print(f"Created {split}.txt with {len(image_list)} images in {list_dir}")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Create list file for change detection dataset')
    
    parser.add_argument('--path', type=str, required=True,
                      help='Path to data directory containing A, B, and label folders')
    
    parser.add_argument('--split', type=str, required=True, choices=['train', 'test', 'val'],
                      help='Dataset split to create (train, test, or val)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Create list file
    create_list(args.path, args.split)

if __name__ == "__main__":
    main() 