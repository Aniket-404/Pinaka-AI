#!/usr/bin/env python3
"""
Dataset Preparation Script for YOLO Custom Training
This script prepares the dataset for training by:
1. Verifying dataset structure
2. Creating dataset configuration
3. Setting up class mappings
"""

import os
import sys
import yaml
import shutil
from pathlib import Path

def main():
    print("🔄 Preparing dataset for YOLO training...")
    
    # Get project root directory
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent.parent
    
    # Define paths
    custom_dataset_dir = root_dir / "custom_dataset"
    models_dir = root_dir / "models"
    dataset_yaml_path = models_dir / "custom_dataset.yaml"
    
    # Verify dataset structure
    print("Checking dataset structure...")
    required_dirs = [
        "custom_dataset/images/train",
        "custom_dataset/images/val",
        "custom_dataset/labels/train",
        "custom_dataset/labels/val"
    ]
    
    for dir_path in required_dirs:
        full_path = root_dir / dir_path
        if not full_path.exists():
            print(f"❌ Required directory not found: {dir_path}")
            return False
    
    # Count images and labels
    train_images = list((custom_dataset_dir / "images" / "train").glob("*.jpg"))
    val_images = list((custom_dataset_dir / "images" / "val").glob("*.jpg"))
    train_labels = list((custom_dataset_dir / "labels" / "train").glob("*.txt"))
    val_labels = list((custom_dataset_dir / "labels" / "val").glob("*.txt"))
    
    print(f"Found {len(train_images)} training images and {len(train_labels)} labels")
    print(f"Found {len(val_images)} validation images and {len(val_labels)} labels")
    
    # Verify custom_dataset.yaml or create if it doesn't exist
    if dataset_yaml_path.exists():
        print(f"Using existing dataset config: {dataset_yaml_path}")
    else:
        print(f"Creating dataset config: {dataset_yaml_path}")
        
        # Define the custom dataset configuration
        dataset_config = {
            "path": ".",  # Relative path, converted to absolute in training
            "train": "custom_dataset/images/train",
            "val": "custom_dataset/images/val",
            "test": "custom_dataset/images/val",  # Use val as test set
            "names": {
                0: "stone",
                1: "gas_cylinder"
            }
        }
        
        # Save the configuration
        with open(dataset_yaml_path, "w") as f:
            yaml.dump(dataset_config, f, default_flow_style=False)
            
        print(f"✅ Created dataset configuration at {dataset_yaml_path}")
    
    # Create .cache files if they don't exist
    cache_files = [
        "custom_dataset/labels/train.cache",
        "custom_dataset/labels/val.cache"
    ]
    
    for cache_file in cache_files:
        cache_path = root_dir / cache_file
        if not cache_path.exists():
            print(f"Note: Cache file {cache_file} not found. Will be created during training.")
    
    # Check if the dataset configuration exists in the models directory
    if dataset_yaml_path.exists():
        # Verify the content
        with open(dataset_yaml_path, "r") as f:
            config_data = yaml.safe_load(f)
            
        # Verify it has the expected structure
        required_keys = ["path", "train", "val", "names"]
        for key in required_keys:
            if key not in config_data:
                print(f"⚠️ Dataset config missing key: {key}")
                print("⚠️ Will be fixed during training")
    
    print("✅ Dataset preparation complete")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
