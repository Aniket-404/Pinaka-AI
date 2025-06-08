#!/usr/bin/env python3
"""
Training Monitoring Script for YOLO Custom Training
This script monitors the progress of YOLO training and displays metrics.
"""

import os
import sys
import yaml
import time
import glob
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def main():
    print("📊 Monitoring YOLO training progress...")
    
    # Get project root directory
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent.parent
    
    # Define paths
    config_path = root_dir / "training" / "config.yaml"
    
    # Load configuration to determine run name
    if config_path.exists():
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            epochs = config.get("epochs", 100)
    else:
        epochs = 100
    
    # Look for the latest training run
    runs_dir = root_dir / "training" / "runs"
    
    if not runs_dir.exists():
        print(f"❌ Training runs directory not found: {runs_dir}")
        print("No training has been started yet.")
        return False
    
    # Find the latest run directory
    run_dirs = list(runs_dir.glob("custom_yolo_*"))
    if not run_dirs:
        print("❌ No training runs found")
        return False
    
    # Sort by modification time to get the latest
    latest_run = max(run_dirs, key=lambda x: x.stat().st_mtime)
    print(f"Found latest training run: {latest_run.name}")
    
    # Check for CSV result files
    results_file = latest_run / "results.csv"
    if not results_file.exists():
        print("❌ No results file found. Training may not have started or is still initializing.")
        return False
    
    # Load and display training progress
    try:
        df = pd.read_csv(results_file)
        
        # Calculate progress
        current_epoch = df["epoch"].max()
        progress_pct = (current_epoch / epochs) * 100
        
        print(f"Training Progress: {current_epoch}/{epochs} epochs ({progress_pct:.1f}%)")
        
        # Display metrics for the latest epoch
        latest = df.iloc[-1]
        print("\nLatest Metrics:")
        print(f"Epoch: {latest['epoch']}")
        
        # Display available metrics
        metrics = [col for col in df.columns if col not in ["epoch", "timestamp"]]
        for metric in metrics:
            if not pd.isna(latest[metric]):
                print(f"{metric}: {latest[metric]:.4f}")
        
        # Generate plots directory
        plots_dir = root_dir / "training" / "results_plots"
        plots_dir.mkdir(exist_ok=True)
        
        # Plot training progress
        if len(df) > 1:  # Need at least 2 points to plot
            plt.figure(figsize=(12, 8))
            
            # Plot loss curves
            loss_cols = [col for col in df.columns if "loss" in col.lower()]
            if loss_cols:
                plt.subplot(2, 1, 1)
                for col in loss_cols:
                    plt.plot(df["epoch"], df[col], label=col)
                plt.title("Training Loss")
                plt.xlabel("Epoch")
                plt.ylabel("Loss")
                plt.legend()
                plt.grid(True)
            
            # Plot metrics
            metric_cols = [col for col in df.columns if "val" in col.lower() and "loss" not in col.lower()]
            if metric_cols:
                plt.subplot(2, 1, 2)
                for col in metric_cols:
                    plt.plot(df["epoch"], df[col], label=col)
                plt.title("Validation Metrics")
                plt.xlabel("Epoch")
                plt.ylabel("Value")
                plt.legend()
                plt.grid(True)
            
            plt.tight_layout()
            plt.savefig(plots_dir / "training_progress.png")
            print(f"\n✅ Saved progress plot to {plots_dir / 'training_progress.png'}")
            plt.close()
        
        print("\n💡 Run this script again to get updated progress")
        return True
    
    except Exception as e:
        print(f"❌ Error monitoring training: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
