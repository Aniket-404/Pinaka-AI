#!/usr/bin/env python3
"""
Model Deployment Script for YOLO Custom Training
This script deploys the trained YOLO model to the application.
"""

import os
import sys
import shutil
import yaml
from pathlib import Path

def main():
    print("📦 Deploying YOLO model...")
    
    # Get project root directory
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent.parent
    
    # Define paths
    models_dir = root_dir / "models"
    
    # Find the best model
    model_pattern = "custom_yolo_*_best.pt"
    model_files = list(models_dir.glob(model_pattern))
    
    if not model_files:
        print(f"❌ No trained model found matching pattern: {model_pattern}")
        print("Please train the model first")
        return False
    
    # Use the latest model file
    source_model_path = max(model_files, key=lambda x: x.stat().st_mtime)
    print(f"Using model: {source_model_path}")
    
    # Define the deployment path
    deployment_model_path = models_dir / "custom_yolo_model.pt"
    
    # Create backup of existing model if it exists
    if deployment_model_path.exists():
        backup_dir = models_dir / "backup"
        backup_dir.mkdir(exist_ok=True)
        
        backup_path = backup_dir / f"{deployment_model_path.name}.bak"
        print(f"Creating backup of existing model: {backup_path}")
        shutil.copy(deployment_model_path, backup_path)
    
    # Copy the model to the deployment location
    print(f"Copying model to deployment location: {deployment_model_path}")
    shutil.copy(source_model_path, deployment_model_path)
    
    # Update model permissions to ensure it's readable
    try:
        os.chmod(deployment_model_path, 0o644)
    except Exception as e:
        print(f"Warning: Could not update model permissions: {e}")
    
    # Generate a simple model info file
    model_info = {
        "name": "Pinaka-AI Custom YOLO Model",
        "source": source_model_path.name,
        "classes": ["stone", "gas_cylinder"],
        "resolution": 640,
        "deployed_at": str(Path(__file__).name)
    }
    
    model_info_path = models_dir / "model_info.yaml"
    with open(model_info_path, "w") as f:
        yaml.dump(model_info, f, default_flow_style=False)
    
    print("\n✅ Model deployment completed successfully")
    print(f"Model deployed to: {deployment_model_path}")
    print(f"Model info saved to: {model_info_path}")
    print("\n🚀 You can now start the application with: python app.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
