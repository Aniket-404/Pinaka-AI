#!/usr/bin/env python3
"""
Model Training Script for YOLO Custom Training
This script trains the YOLO model on the custom dataset.
"""

import os
import sys
import yaml
import torch
from pathlib import Path

def main():
    print("🚀 Starting YOLO model training...")
    
    # Get project root directory
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent.parent
    
    # Define paths
    config_path = root_dir / "training" / "config.yaml"
    models_dir = root_dir / "models"
    dataset_yaml_path = models_dir / "custom_dataset.yaml"
    
    # Verify config file exists
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        # Create a default config if it doesn't exist
        create_default_config(config_path)
    
    # Load configuration
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    # Check if dataset YAML exists
    if not dataset_yaml_path.exists():
        print(f"❌ Dataset configuration not found: {dataset_yaml_path}")
        print("Please run the prepare dataset script first")
        return False
    
    # Determine device (CUDA or CPU)
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f"Training on device: {device}")
    
    # Get training parameters
    epochs = config.get("epochs", 100)
    batch_size = config.get("batch", 16)
    image_size = config.get("img_size", 640)
    
    print(f"Training for {epochs} epochs with batch size {batch_size}")
    print(f"Image size: {image_size}")
    
    # Set up output directory
    run_name = f"custom_yolo_{epochs}epochs_{'cuda' if 'cuda' in device else 'cpu'}"
    output_dir = root_dir / "training" / "runs" / run_name
    
    # Import YOLO here to avoid loading it if configuration checks fail
    try:
        from ultralytics import YOLO
    except ImportError:
        print("❌ Error: Ultralytics package not found")
        print("Please install it with: pip install ultralytics")
        return False
    
    # Initialize model
    try:
        print("Initializing YOLOv8 model...")
        model = YOLO("yolov8n.pt")  # Start with pretrained model
        
        # Start training
        print(f"Starting training for {epochs} epochs...")
        
        # Convert dataset path to absolute path for YOLO
        dataset_yaml_abs = str(dataset_yaml_path.absolute())
        
        results = model.train(
            data=dataset_yaml_abs,
            epochs=epochs,
            batch=batch_size,
            imgsz=image_size,
            device=device,
            name=run_name,
            project=str(root_dir / "training" / "runs")
        )
        
        # Copy the best model to models directory
        best_model_path = output_dir / "weights" / "best.pt"
        if best_model_path.exists():
            target_path = models_dir / f"custom_yolo_{epochs}epochs_best.pt"
            import shutil
            shutil.copy(best_model_path, target_path)
            print(f"✅ Copied best model to {target_path}")
        
        # Copy the final model to models directory
        final_model_path = output_dir / "weights" / "last.pt"
        if final_model_path.exists():
            target_path = models_dir / f"custom_yolo_{epochs}epochs_final.pt"
            import shutil
            shutil.copy(final_model_path, target_path)
            print(f"✅ Copied final model to {target_path}")
        
        print("✅ Training completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error during training: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_default_config(config_path):
    """Create a default configuration file"""
    default_config = {
        "epochs": 100,
        "batch": 16,
        "img_size": 640,
        "patience": 50,
        "save_period": 10
    }
    
    # Create directory if it doesn't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write the configuration
    with open(config_path, "w") as f:
        yaml.dump(default_config, f, default_flow_style=False)
    
    print(f"✅ Created default configuration at {config_path}")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
