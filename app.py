import os
from flask import Flask, render_template, redirect, url_for, flash, Response, jsonify
from flask_socketio import SocketIO
from app.forms import NotificationForm
from app.utils.config import Config
from dotenv import load_dotenv
import cv2
import time
import traceback

# Load environment variables
load_dotenv()

# Set Ultralytics config directory if not already set
if 'YOLO_CONFIG_DIR' not in os.environ:
    os.environ['YOLO_CONFIG_DIR'] = '/tmp/yolo_config'
    
# Create the directory if it doesn't exist
if not os.path.exists(os.environ['YOLO_CONFIG_DIR']):
    os.makedirs(os.environ['YOLO_CONFIG_DIR'], exist_ok=True)

# Disable Ultralytics cache downloads
os.environ['ULTRALYTICS_NO_CACHE'] = '1'

# Create Flask app with correct template folder
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'app', 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'app', 'static'))
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
socketio = SocketIO(app)

# Check if we're in production environment
is_production = os.environ.get('RENDER', False)

# Only import the ObjectDetector class after setting environment variables
from app.utils.object_detector import ObjectDetector

# Model paths
custom_model_path = "models/custom_yolo_100epochs_best.pt"
coco_model_path = "models/yolov8n.pt"

# Initialize detectors
custom_detector = None
coco_detector = None

def initialize_model(model_path, name="model", max_retries=2, retry_delay=2):
    """Initialize a model with retry logic"""
    for attempt in range(max_retries + 1):
        try:
            print(f"Attempting to load {name} (attempt {attempt+1}/{max_retries+1}): {model_path}")
            detector = ObjectDetector(model_path=model_path, socketio=socketio)
            if detector.model_loaded:
                print(f"{name} loaded successfully")
                return detector
            else:
                print(f"{name} initialization returned False for model_loaded")
                if attempt < max_retries:
                    print(f"Will retry in {retry_delay} seconds...")
                    time.sleep(retry_delay)
        except Exception as e:
            print(f"Error loading {name}: {e}")
            if attempt < max_retries:
                print(f"Will retry in {retry_delay} seconds...")
                time.sleep(retry_delay)
    
    # If we get here, all attempts failed
    print(f"All attempts to load {name} failed, using fallback")
    return ObjectDetector(use_fallback=True)

# If in production mode, use simplified demo detectors
if is_production:
    print("Running in production mode, using simplified detectors")
    custom_detector = ObjectDetector(use_fallback=True)
    coco_detector = ObjectDetector(use_fallback=True)
else:
    # In development mode, try to load the actual models with retry logic
    custom_detector = initialize_model(custom_model_path, "custom model")
    coco_detector = initialize_model(coco_model_path, "COCO model")

# Config for detection settings
config = Config()

# Helper to get the active detector

def get_active_detector():
    if config.selected_model == "custom" and custom_detector and custom_detector.model_loaded:
        return custom_detector
    elif config.selected_model == "coco" and coco_detector and coco_detector.model_loaded:
        return coco_detector
    # fallback
    return custom_detector if custom_detector and custom_detector.model_loaded else coco_detector

@app.route('/health')
def health_check():
    """Enhanced health check endpoint for Render"""
    import platform
    import psutil
    
    # Memory usage stats
    memory = psutil.virtual_memory()
    
    status = {
        "status": "healthy",
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "custom_model": {
            "loaded": custom_detector.model_loaded if custom_detector else False,
            "demo_mode": hasattr(custom_detector, 'demo_mode') and custom_detector.demo_mode if custom_detector else True,
        },
        "coco_model": {
            "loaded": coco_detector.model_loaded if coco_detector else False,
            "demo_mode": hasattr(coco_detector, 'demo_mode') and coco_detector.demo_mode if coco_detector else True,
        },
        "system": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "memory_percent": memory.percent,
            "memory_available_mb": memory.available / (1024 * 1024),
        },
        "environment": {
            "production_mode": bool(os.environ.get('RENDER', False)),
            "ultralytics_cache": os.environ.get('ULTRALYTICS_NO_CACHE', 'not set'),
            "yolo_config_dir": os.environ.get('YOLO_CONFIG_DIR', 'not set'),
        },
        "version": "1.1.0"
    }
    return jsonify(status)

@app.errorhandler(500)
def server_error(e):
    """Handle server errors gracefully"""
    error_details = traceback.format_exc()
    print(f"Server Error: {error_details}")
    return render_template('error.html', error=str(e), details=error_details), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    form = NotificationForm()
    # Get available classes from both models
    available_classes = set()
    if custom_detector and custom_detector.model_loaded and hasattr(custom_detector.model, 'names'):
        available_classes.update(list(custom_detector.model.names.values()))
    if coco_detector and coco_detector.model_loaded and hasattr(coco_detector.model, 'names'):
        available_classes.update(list(coco_detector.model.names.values()))
    if "Movement" not in available_classes:
        available_classes.add("Movement")
    for custom_class in ["stone", "gas_cylinder"]:
        available_classes.add(custom_class)
    available_classes = sorted(available_classes)

    if form.validate_on_submit():
        config.monitored_objects = [c.strip() for c in form.monitored_objects.data.split(',') if c.strip()]
        config.notification_threshold = form.confidence_threshold.data
        config.selected_model = form.selected_model.data
        flash('Settings saved successfully!', 'success')
        return redirect(url_for('index'))
    if not form.is_submitted():
        form.monitored_objects.data = ','.join(config.monitored_objects)
        form.confidence_threshold.data = config.notification_threshold
        form.selected_model.data = config.selected_model
    return render_template('settings.html', form=form, available_classes=available_classes)

@app.route('/video_feed')
def video_feed():
    # Check if we're in a production environment (like Render)
    is_production = os.environ.get('RENDER', False)
    
    def generate_frames():
        while True:
            frame = None
            ret = False
            # Prefer custom detector for camera/demo frame
            if custom_detector:
                custom_detector._ensure_camera_open()
                if hasattr(custom_detector, 'demo_mode') and custom_detector.demo_mode:
                    frame = custom_detector.demo_frame.copy()
                    ret = True
                else:
                    ret, frame = custom_detector.cap.read()
            elif coco_detector:
                coco_detector._ensure_camera_open()
                if hasattr(coco_detector, 'demo_mode') and coco_detector.demo_mode:
                    frame = coco_detector.demo_frame.copy()
                    ret = True
                else:
                    ret, frame = coco_detector.cap.read()
            else:
                break
            if not ret or frame is None:
                break
            # Always run both detectors
            frame_custom, detected_custom = (frame.copy(), [])
            frame_coco, detected_coco = (frame.copy(), [])
            if custom_detector and custom_detector.model_loaded:
                frame_custom, detected_custom = custom_detector._process_frame(frame.copy(), config)
            if coco_detector and coco_detector.model_loaded:
                frame_coco, detected_coco = coco_detector._process_frame(frame.copy(), config)
            # Merge detections (simple concat, or you can deduplicate if needed)
            all_detections = detected_custom + detected_coco
            # For display: overlay custom detections if any, else coco, else original
            if detected_custom:
                out_frame = frame_custom
            elif detected_coco:
                out_frame = frame_coco
            else:
                out_frame = frame
            ret, buffer = cv2.imencode('.jpg', out_frame)
            if not ret:
                continue
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            if is_production or (hasattr(custom_detector, 'demo_mode') and custom_detector.demo_mode):
                time.sleep(0.1)
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    # Use this for local development
    socketio.run(app, debug=True)
    
# This is needed for Render deployment with gunicorn
# The application variable for gunicorn to use
application = app