"""
Initialization script to set up environment variables and directories
for the Pinaka-AI application. This script is used by Render during deployment.
"""
import os
import sys
import shutil
import urllib.request

def setup_environment():
    """Set up environment variables and directories for YOLO models"""
    # Disable Ultralytics cache downloads
    os.environ['ULTRALYTICS_NO_CACHE'] = '1'
    print("Disabled Ultralytics cache downloads (ULTRALYTICS_NO_CACHE=1)")
    
    # Set XDG_CONFIG_HOME to a writable location
    os.environ['XDG_CONFIG_HOME'] = '/tmp/.config'
    print(f"Set XDG_CONFIG_HOME to {os.environ['XDG_CONFIG_HOME']}")
    
    # Create XDG_CONFIG_HOME directory
    if not os.path.exists(os.environ['XDG_CONFIG_HOME']):
        os.makedirs(os.environ['XDG_CONFIG_HOME'], exist_ok=True)
        print(f"Created directory: {os.environ['XDG_CONFIG_HOME']}")
    
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
        
    # Check for models and download if needed
    model_paths = {
        'yolov8n.pt': 'https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt'
    }
    
    for model_name, url in model_paths.items():
        local_path = os.path.join('models', model_name)
        tmp_path = os.path.join(tmp_models_dir, model_name)
        
        # If model doesn't exist in the local models directory but exists in tmp, copy it
        if not os.path.exists(local_path) and os.path.exists(tmp_path):
            try:
                shutil.copy2(tmp_path, local_path)
                print(f"Copied {model_name} from {tmp_path} to {local_path}")
            except Exception as e:
                print(f"Error copying model {model_name}: {e}")
                
        # If model doesn't exist anywhere, download it
        if not os.path.exists(local_path):
            try:
                print(f"Downloading {model_name} from {url}...")
                # Ensure the models directory exists
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                urllib.request.urlretrieve(url, local_path)
                print(f"Successfully downloaded {model_name}")
                
                # Also save a copy to tmp directory
                shutil.copy2(local_path, tmp_path)
                print(f"Saved a copy to {tmp_path}")
            except Exception as e:
                print(f"Error downloading model {model_name}: {e}")
    
    # Make sure the script directory is in the Python path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.append(script_dir)
        print(f"Added {script_dir} to Python path")

if __name__ == "__main__":
    setup_environment()
