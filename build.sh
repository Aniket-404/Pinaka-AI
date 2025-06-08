#!/bin/bash
# Build script for Render deployment

# Create YOLO config directory
mkdir -p /tmp/yolo_config
echo "Created YOLO config directory: /tmp/yolo_config"

# Create models directory
mkdir -p /tmp/models
echo "Created models directory: /tmp/models"

# Disable cache downloads for Ultralytics
export ULTRALYTICS_NO_CACHE=1
echo "Disabled Ultralytics cache downloads (ULTRALYTICS_NO_CACHE=1)"

# Create a .config directory to prevent cache attempts
mkdir -p /tmp/.config
export XDG_CONFIG_HOME=/tmp/.config
echo "Set XDG_CONFIG_HOME to /tmp/.config"

# Upgrade pip and install dependencies
pip install --upgrade pip
echo "Installing dependencies..."
pip install -r requirements.txt

# Run initialization script
python init_env.py

# Download YOLOv8n model directly if needed
if [ ! -f "models/yolov8n.pt" ]; then
    echo "Downloading YOLOv8n model directly..."
    mkdir -p models
    wget -q https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt -O models/yolov8n.pt
    if [ $? -eq 0 ]; then
        echo "YOLOv8n model downloaded successfully"
    else
        echo "Failed to download YOLOv8n model"
    fi
fi

echo "Build completed successfully!"
