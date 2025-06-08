"""
Initialization script to set up environment variables and directories
for the Pinaka-AI application. This script is used by Render during deployment.
"""
import os
import sys

def setup_environment():
    """Set up environment variables and directories for YOLO models"""
    # Set Ultralytics config directory if not already set
    if 'YOLO_CONFIG_DIR' not in os.environ:
        os.environ['YOLO_CONFIG_DIR'] = '/tmp/yolo_config'
        print(f"Setting YOLO_CONFIG_DIR to {os.environ['YOLO_CONFIG_DIR']}")
    
    # Create the directory if it doesn't exist
    if not os.path.exists(os.environ['YOLO_CONFIG_DIR']):
        os.makedirs(os.environ['YOLO_CONFIG_DIR'], exist_ok=True)
        print(f"Created directory: {os.environ['YOLO_CONFIG_DIR']}")
    
    # Create a models directory in /tmp if it doesn't exist
    tmp_models_dir = '/tmp/models'
    if not os.path.exists(tmp_models_dir):
        os.makedirs(tmp_models_dir, exist_ok=True)
        print(f"Created directory: {tmp_models_dir}")
    
    # Make sure the script directory is in the Python path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.append(script_dir)
        print(f"Added {script_dir} to Python path")

if __name__ == "__main__":
    setup_environment()
