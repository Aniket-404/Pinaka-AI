#!/usr/bin/env python3
"""
Master Training Script - Complete YOLO Custom Training Pipeline
This script orchestrates the entire training process from start to finish.
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

class TrainingPipeline:
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.root_dir = self.script_dir.parent.parent
        self.scripts = {
            'prepare': self.script_dir / "01_prepare_dataset.py",
            'train': self.script_dir / "02_train_model.py", 
            'monitor': self.script_dir / "03_monitor_training.py",
            'test': self.script_dir / "04_test_model.py",
            'deploy': self.script_dir / "05_deploy_model.py"
        }
    
    def run_script(self, script_name, args=None):
        """Run a training pipeline script"""
        script_path = self.scripts.get(script_name)
        
        if not script_path or not script_path.exists():
            print(f"❌ Script not found: {script_name}")
            return False
        
        print(f"\n🔄 Running: {script_name}")
        print("=" * 50)
        
        try:
            cmd = [sys.executable, str(script_path)]
            if args:
                cmd.extend(args)
            
            result = subprocess.run(cmd, cwd=self.root_dir, check=True)
            print(f"✅ {script_name} completed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ {script_name} failed with exit code: {e.returncode}")
            return False
        except Exception as e:
            print(f"❌ Error running {script_name}: {e}")
            return False
    
    def check_prerequisites(self):
        """Check if all prerequisites are met"""
        print("🔧 Checking Prerequisites...")
        
        # Check if dataset exists
        dataset_dir = self.root_dir / "custom_dataset"
        if not dataset_dir.exists():
            print("❌ Custom dataset not found")
            print("💡 Please organize your dataset first using organize_datasets.py")
            return False
        
        # Check if required directories exist
        required_dirs = [
            "custom_dataset/images/train",
            "custom_dataset/images/val", 
            "custom_dataset/labels/train",
            "custom_dataset/labels/val"
        ]
        
        for dir_path in required_dirs:
            full_path = self.root_dir / dir_path
            if not full_path.exists():
                print(f"❌ Required directory not found: {dir_path}")
                return False
        
        print("✅ Prerequisites check passed")
        return True
    
    def run_full_pipeline(self):
        """Run the complete training pipeline"""
        print("🎯 YOLO Custom Training - Full Pipeline")
        print("=" * 60)
        print("📋 Pipeline Steps:")
        print("   1. Prepare Dataset")
        print("   2. Train Model")
        print("   3. Test Model") 
        print("   4. Deploy Model")
        print("=" * 60)
        
        # Check prerequisites
        if not self.check_prerequisites():
            return False
        
        # Step 1: Prepare dataset
        if not self.run_script('prepare'):
            print("❌ Pipeline failed at dataset preparation")
            return False
        
        # Step 2: Train model
        print("\n🚀 Starting model training...")
        print("⚠️  This may take a while (30-60 minutes)")
        print("💡 You can monitor progress with: python training/scripts/03_monitor_training.py")
        
        if not self.run_script('train'):
            print("❌ Pipeline failed at model training")
            return False
        
        # Step 3: Test model
        if not self.run_script('test', ['--validation', '--samples', '--benchmark']):
            print("⚠️ Model testing failed, but continuing...")
        
        # Step 4: Deploy model
        if not self.run_script('deploy'):
            print("❌ Pipeline failed at model deployment")
            return False
        
        print("\n" + "🎉" * 20)
        print("✅ COMPLETE TRAINING PIPELINE FINISHED!")
        print("🎉" * 20)
        print("🏆 Your custom YOLO model is trained and deployed!")
        print("🔧 Custom classes: stone, gas_cylinder")
        print("🚀 Start the application: python app.py")
        print("🧪 Test with webcam: python training/scripts/04_test_model.py --webcam")
        
        return True
    
    def run_quick_train(self):
        """Run quick training with minimal epochs for testing"""
        print("⚡ Quick Training Mode")
        print("=" * 30)
        print("This will train for only 10 epochs for quick testing")
        
        # Modify config for quick training
        config_path = self.root_dir / "training/config.yaml"
        if config_path.exists():
            # Read current config
            with open(config_path, 'r') as f:
                content = f.read()
            
            # Backup original
            backup_path = config_path.with_suffix('.yaml.backup')
            with open(backup_path, 'w') as f:
                f.write(content)
            
            # Modify for quick training
            content = content.replace('epochs: 50', 'epochs: 10')
            content = content.replace('batch: 16', 'batch: 8')
            
            with open(config_path, 'w') as f:
                f.write(content)
            
            print("⚙️ Modified config for quick training (10 epochs)")
        
        # Run training
        success = self.run_script('train')
        
        # Restore original config
        if config_path.exists() and backup_path.exists():
            with open(backup_path, 'r') as f:
                original_content = f.read()
            with open(config_path, 'w') as f:
                f.write(original_content)
            backup_path.unlink()
            print("⚙️ Restored original config")
        
        return success

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YOLO Custom Training Pipeline')
    parser.add_argument('--step', choices=['prepare', 'train', 'test', 'deploy'], 
                        help='Run specific pipeline step')
    parser.add_argument('--quick', action='store_true', 
                        help='Quick training mode (10 epochs)')
    parser.add_argument('--monitor', action='store_true',
                        help='Monitor training progress')
    parser.add_argument('--test-webcam', action='store_true',
                        help='Test model on webcam')
    
    args = parser.parse_args()
    
    pipeline = TrainingPipeline()
    
    # Change to project root
    os.chdir(pipeline.root_dir)
    
    if args.step:
        # Run specific step
        success = pipeline.run_script(args.step)
    elif args.quick:
        # Quick training mode
        success = pipeline.run_quick_train()
    elif args.monitor:
        # Monitor training
        success = pipeline.run_script('monitor')
    elif args.test_webcam:
        # Test on webcam
        success = pipeline.run_script('test', ['--webcam'])
    else:
        # Run full pipeline
        success = pipeline.run_full_pipeline()
    
    return success

if __name__ == "__main__":
    main()
