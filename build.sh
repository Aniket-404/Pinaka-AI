#!/bin/bash
# Build script for Render deployment

echo "Starting build process for Pinaka-AI deployment..."

# Set environment variables for the build
export RENDER=true
export ULTRALYTICS_NO_CACHE=1
export XDG_CONFIG_HOME=/tmp/.config
export YOLO_CONFIG_DIR=/tmp/yolo_config
export PYTORCH_NO_CUDA_MEMORY_CACHING=1
export CUDA_VISIBLE_DEVICES=

echo "Environment variables set:"
echo "- RENDER: $RENDER"
echo "- ULTRALYTICS_NO_CACHE: $ULTRALYTICS_NO_CACHE"
echo "- YOLO_CONFIG_DIR: $YOLO_CONFIG_DIR"

# Create necessary directories
mkdir -p /tmp/yolo_config
mkdir -p /tmp/.config
mkdir -p /tmp/models
echo "Created necessary directories"

# Upgrade pip and install dependencies
echo "Upgrading pip and installing dependencies..."
pip install --upgrade pip

# Check if we're in a memory-constrained environment (Render free tier)
MEMORY=$(free -m | awk '/^Mem:/{print $2}')
echo "Available memory: $MEMORY MB"

if [ $MEMORY -lt 2000 ]; then
    echo "Detected low memory environment, using production-optimized requirements"
    pip install -r requirements-prod.txt
else
    echo "Installing full requirements"
    pip install -r requirements.txt
fi

# Run initialization script
python init_env.py

echo "Build completed successfully!"
