#!/bin/bash
# Build script for Render deployment

# Create YOLO config directory
mkdir -p /tmp/yolo_config
echo "Created YOLO config directory: /tmp/yolo_config"

# Create models directory
mkdir -p /tmp/models
echo "Created models directory: /tmp/models"

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run initialization script
python init_env.py

echo "Build completed successfully!"
