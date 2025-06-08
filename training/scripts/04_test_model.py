#!/usr/bin/env python3
"""
Model Testing Script for YOLO Custom Training
This script tests the trained YOLO model on validation data or webcam.
"""

import os
import sys
import cv2
import yaml
import torch
import argparse
from pathlib import Path

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Test YOLO model")
    parser.add_argument("--validation", action="store_true", help="Run validation on the validation set")
    parser.add_argument("--samples", action="store_true", help="Generate sample detection images")
    parser.add_argument("--benchmark", action="store_true", help="Run benchmarking tests")
    parser.add_argument("--webcam", action="store_true", help="Test on webcam")
    args = parser.parse_args()
    
    # Default to validation if no args specified
    if not any(vars(args).values()):
        args.validation = True
    
    print("🧪 Testing YOLO model...")
    
    # Get project root directory
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent.parent
    
    # Define paths
    models_dir = root_dir / "models"
    dataset_yaml_path = models_dir / "custom_dataset.yaml"
    
    # Find the best model
    model_pattern = "custom_yolo_*_best.pt"
    model_files = list(models_dir.glob(model_pattern))
    
    if not model_files:
        print(f"❌ No trained model found matching pattern: {model_pattern}")
        print("Please train the model first")
        return False
    
    # Use the latest model file
    model_path = max(model_files, key=lambda x: x.stat().st_mtime)
    print(f"Using model: {model_path}")
    
    # Import YOLO
    try:
        from ultralytics import YOLO
    except ImportError:
        print("❌ Error: Ultralytics package not found")
        print("Please install it with: pip install ultralytics")
        return False
    
    # Load the model
    try:
        model = YOLO(str(model_path))
        
        # Run validation if requested
        if args.validation:
            print("\n🔍 Running validation on validation set...")
            if not dataset_yaml_path.exists():
                print(f"❌ Dataset configuration not found: {dataset_yaml_path}")
                return False
            
            metrics = model.val(data=str(dataset_yaml_path.absolute()))
            
            # Display validation results
            if metrics:
                print("\nValidation Results:")
                for k, v in metrics.items():
                    if isinstance(v, (int, float)):
                        print(f"{k}: {v:.4f}")
        
        # Generate sample detections if requested
        if args.samples:
            print("\n🖼️ Generating sample detections...")
            val_img_dir = root_dir / "custom_dataset" / "images" / "val"
            
            if not val_img_dir.exists() or not list(val_img_dir.glob("*.jpg")):
                print(f"❌ No validation images found in {val_img_dir}")
            else:
                # Use up to 5 random validation images
                import random
                sample_imgs = list(val_img_dir.glob("*.jpg"))
                sample_imgs = random.sample(sample_imgs, min(5, len(sample_imgs)))
                
                # Run prediction on sample images
                for img_path in sample_imgs:
                    print(f"Generating detection for {img_path.name}...")
                    results = model.predict(
                        source=str(img_path), 
                        save=True,
                        project=str(root_dir / "training" / "results_plots"),
                        name="sample_detections"
                    )
                
                print(f"✅ Sample detections saved to {root_dir / 'training' / 'results_plots' / 'sample_detections'}")
        
        # Run benchmarking if requested
        if args.benchmark:
            print("\n⏱️ Running benchmark tests...")
            
            # Load a sample image for benchmarking
            val_img_dir = root_dir / "custom_dataset" / "images" / "val"
            if not val_img_dir.exists() or not list(val_img_dir.glob("*.jpg")):
                print(f"❌ No validation images found in {val_img_dir}")
            else:
                # Use the first image for benchmarking
                sample_img = next(val_img_dir.glob("*.jpg"))
                
                # Load the image
                img = cv2.imread(str(sample_img))
                
                # Warm up
                for _ in range(5):
                    _ = model.predict(source=img, verbose=False)
                
                # Benchmark
                import time
                times = []
                for _ in range(20):
                    start_time = time.time()
                    _ = model.predict(source=img, verbose=False)
                    end_time = time.time()
                    times.append(end_time - start_time)
                
                # Calculate statistics
                avg_time = sum(times) / len(times)
                fps = 1 / avg_time
                
                print(f"Average inference time: {avg_time:.4f} seconds")
                print(f"Frames per second: {fps:.2f} FPS")
        
        # Test on webcam if requested
        if args.webcam:
            print("\n📹 Testing on webcam...")
            print("Press 'q' to quit")
            
            # Run the model on webcam
            model.predict(source=0, show=True)
        
        print("\n✅ Testing completed successfully")
        return True
    
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
