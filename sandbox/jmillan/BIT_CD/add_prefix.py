import os
from pathlib import Path
import argparse

def add_prefix(folder_path, prefix):
    """Add prefix to all files in a folder.
    
    Args:
        folder_path (str): Path to folder containing files
        prefix (str): Prefix to add to filenames
    """
    folder = Path(folder_path)
    
    if not folder.exists():
        raise FileNotFoundError(f"Directory not found at {folder}")
        
    # Get all files from directory
    files = sorted(folder.glob("*"))
    
    # Rename each file
    for file_path in files:
        # Skip if already has prefix
        if file_path.stem.startswith(prefix):
            continue
            
        # Create new filename with prefix
        new_name = f"{prefix}{file_path.name}"
        new_path = folder / new_name
        
        # Rename file
        file_path.rename(new_path)
        print(f"Renamed {file_path.name} to {new_name}")

def main():
    parser = argparse.ArgumentParser(description='Add prefix to all files in a folder')
    
    parser.add_argument('--folder', type=str, required=True,
                      help='Path to folder containing files')
    
    parser.add_argument('--prefix', type=str, required=True,
                      help='Prefix to add to filenames')
    
    args = parser.parse_args()
    
    add_prefix(args.folder, args.prefix)

if __name__ == "__main__":
    main() 