# Pinaka AI - Object Detection System

A real-time object detection system using YOLOv8 and Flask, with browser notifications for detected objects.

## Features

- Real-time object detection using YOLOv8
- Browser notifications for detected objects
- Configurable object monitoring
- Fallback motion detection mode
- Web interface for settings and monitoring

## Prerequisites

- Python 3.8+
- Git LFS (for handling large model files)
- Webcam or video source

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pinaka-ai.git
cd pinaka-ai
```

2. Install Git LFS:
```bash
# Windows (using Chocolatey - Run PowerShell as Administrator)
choco install git-lfs

# Or download manually from: https://git-lfs.github.com/
```

3. Initialize Git LFS:
```bash
git lfs install
```

4. Download the YOLOv8 model:
```bash
# Create the models directory if it doesn't exist
mkdir -p app/models

# Download the YOLOv8n model
curl -L https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt -o app/models/yolov8n.pt
```

5. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

6. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the application:
```bash
python app.py
```

2. Open your browser and navigate to `http://localhost:5000`

3. Configure detection settings in the Settings page:
   - Select objects to monitor
   - Adjust confidence threshold
   - Save settings

4. View the video feed and receive notifications for detected objects

## Model Files

The project uses the YOLOv8n model, which needs to be downloaded manually. The model file is not included in the repository due to its large size. Follow the installation instructions above to download the model.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 