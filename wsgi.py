# Import app directly from app.py to avoid confusion with the app package
import importlib.util
import os
import sys

# Mark this as a production environment
os.environ['RENDER'] = 'true'

# Disable CUDA to save memory
os.environ['CUDA_VISIBLE_DEVICES'] = ''

# Disable Torch optimization for deployment
os.environ['PYTORCH_NO_CUDA_MEMORY_CACHING'] = '1'

# Configure paths for logging and temporary files
os.environ['TMPDIR'] = '/tmp'

# Set up other environment variables
os.environ['ULTRALYTICS_NO_CACHE'] = '1'
os.environ['YOLO_CONFIG_DIR'] = '/tmp/yolo_config'
os.environ['XDG_CONFIG_HOME'] = '/tmp/.config'

# Get port from environment
port = int(os.environ.get("PORT", 10000))
print(f"Using port: {port}")

# Create necessary directories
for directory in ['/tmp/yolo_config', '/tmp/.config', '/tmp/models']:
    os.makedirs(directory, exist_ok=True)

# Print environment for debugging
print("WSGI Environment:")
print(f"- RENDER: {os.environ.get('RENDER')}")
print(f"- YOLO_CONFIG_DIR: {os.environ.get('YOLO_CONFIG_DIR')}")
print(f"- ULTRALYTICS_NO_CACHE: {os.environ.get('ULTRALYTICS_NO_CACHE')}")
print(f"- PORT: {port}")

# Run environment initialization
try:
    from init_env import setup_environment
    setup_environment()
except Exception as e:
    print(f"Error running environment setup: {e}")

# Load app.py using a more memory-efficient approach
print("Loading application...")
try:
    # Directly load the app.py module
    spec = importlib.util.spec_from_file_location("app_module", 
                                                os.path.join(os.path.dirname(__file__), "app.py"))
    app_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_module)
    
    # Get app and socketio from the loaded module
    app = app_module.app
    socketio = app_module.socketio
    # Do NOT define /health here; it is defined in app.py
    print("Application loaded successfully")
except Exception as e:
    print(f"Error loading application: {e}")
    raise

# Export the app variable for gunicorn
application = app

# If running directly (not through gunicorn)
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=port)