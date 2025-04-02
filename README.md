# Pinaka AI - Real-time Object Detection System 🎯

A powerful real-time object detection system using YOLOv8 and Flask, with browser notifications for detected objects. Monitor your surroundings with AI-powered detection and instant alerts! 🚀

## ✨ Features

- 🔍 Real-time object detection using YOLOv8
- 📱 Support for both webcam and mobile camera (via DroidCam)
- 🔔 Browser notifications for detected objects
- ⚙️ Customizable object monitoring
- 🎨 Modern, responsive web interface
- 📊 Real-time confidence scores
- 📸 Snapshot capture of detected objects
- 🔄 Fallback motion detection mode

## 🛠️ Prerequisites

- Python 3.8 or higher
- Git LFS (for handling large model files)
- Webcam or mobile camera
- Modern web browser with JavaScript enabled

## 📦 Installation

1. **Clone the repository** 🏗️
```bash
git clone https://github.com/yourusername/pinaka-ai.git
cd pinaka-ai
```

2. **Install Git LFS** 📥
```bash
# Windows (using Chocolatey - Run PowerShell as Administrator)
choco install git-lfs

# Or download manually from: https://git-lfs.github.com/
```

3. **Initialize Git LFS** 🔄
```bash
git lfs install
```

4. **Download the YOLOv8 model** 🤖
```bash
# Create the models directory if it doesn't exist
mkdir -p app/models

# Download the YOLOv8n model
curl -L https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt -o app/models/yolov8n.pt
```

5. **Create and activate virtual environment** 🌐
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

6. **Install dependencies** 📚
```bash
pip install -r requirements.txt
```

## 🚀 Usage

1. **Start the application** ▶️
```bash
python app.py
```

2. **Access the web interface** 🌐
- Open your browser and navigate to `http://localhost:5000`
- Allow browser notifications when prompted

3. **Configure detection settings** ⚙️
- Go to the Settings page
- Select objects to monitor (e.g., person, car, dog)
- Adjust confidence threshold (0.1-1.0)
- Save your settings

4. **Using mobile camera (optional)** 📱
- Install DroidCam app on your phone
  - Android: [Google Play Store](https://play.google.com/store/apps/details?id=com.dev47apps.droidcam)
  - iOS: [App Store](https://apps.apple.com/us/app/droidcam-wireless-webcam/id1510258105)
- Install DroidCam client on your laptop
  - Download from [DroidCam website](https://www.dev47apps.com/)
- Connect both devices to the same WiFi network
- Start DroidCam on your phone and note the IP address
- Enter the IP in DroidCam client on your laptop
- The system will automatically detect and use DroidCam

## 🎯 Detection Features

- Real-time object detection with bounding boxes
- Confidence scores for each detection
- Browser notifications with snapshots
- Customizable object monitoring
- Motion detection fallback mode
- Responsive web interface

## ⚙️ Configuration Options

- **Monitored Objects**: Select which objects to detect
- **Confidence Threshold**: Adjust detection sensitivity
- **Notification Cooldown**: Control notification frequency
- **Camera Selection**: Choose between webcam and DroidCam

## 🐛 Troubleshooting

1. **Camera not detected** 🔍
   - Ensure your camera is properly connected
   - Check if DroidCam is running (if using mobile camera)
   - Try refreshing the page

2. **Model not loading** 🤖
   - Verify the YOLOv8 model is downloaded
   - Check if you have sufficient disk space
   - Ensure Python version is compatible

3. **Notifications not working** 🔔
   - Allow browser notifications
   - Check browser settings
   - Try using a different browser

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🙏 Acknowledgments

- YOLOv8 by Ultralytics
- Flask web framework
- OpenCV for image processing
- DroidCam for mobile camera support

---