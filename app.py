import os
from flask import Flask, render_template, redirect, url_for, flash, Response
from flask_socketio import SocketIO
from app.forms import NotificationForm
from app.utils.object_detector import ObjectDetector
from app.utils.config import Config
from dotenv import load_dotenv
import cv2
import time

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

# Load both models
custom_model_path = "models/custom_yolo_100epochs_best.pt"
coco_model_path = "models/yolov8n.pt"

custom_detector = None
coco_detector = None

# Check if we're in production environment
is_production = os.environ.get('RENDER', False)

try:
    print(f"Attempting to load custom model: {custom_model_path}")
    custom_detector = ObjectDetector(model_path=custom_model_path, socketio=socketio)
    if custom_detector.model_loaded:
        print(f"Custom model loaded with classes: {list(custom_detector.model.names.values())}")
    else:
        print("Custom model failed to load. Using demo mode.")
        if is_production:
            # In production, ensure we have a demo mode detector
            custom_detector.demo_mode = True
except Exception as e:
    print(f"Error loading custom model: {e}")
    # Create a fallback detector in demo mode
    custom_detector = ObjectDetector(use_fallback=True)
    custom_detector.demo_mode = True

try:
    print(f"Attempting to load COCO model: {coco_model_path}")
    coco_detector = ObjectDetector(model_path=coco_model_path, socketio=socketio)
    if coco_detector.model_loaded:
        print(f"COCO model loaded with classes: {list(coco_detector.model.names.values())}")
    else:
        print("COCO model failed to load. Using demo mode.")
        if is_production:
            # In production, ensure we have a demo mode detector
            coco_detector.demo_mode = True
except Exception as e:
    print(f"Error loading COCO model: {e}")
    # Create a fallback detector in demo mode
    coco_detector = ObjectDetector(use_fallback=True)
    coco_detector.demo_mode = True

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    form = NotificationForm()
    # Remove model selection logic
    # Get available classes from both models
    available_classes = set()
    if custom_detector and custom_detector.model_loaded and hasattr(custom_detector.model, 'names'):
        available_classes.update(list(custom_detector.model.names.values()))
    if coco_detector and coco_detector.model_loaded and hasattr(coco_detector.model, 'names'):
        available_classes.update(list(coco_detector.model.names.values()))
    if "Movement" not in available_classes:
        available_classes.add("Movement")
    # Always ensure custom classes appear
    for custom_class in ["stone", "gas_cylinder"]:
        available_classes.add(custom_class)
    available_classes = sorted(available_classes)

    if form.validate_on_submit():
        config.monitored_objects = form.monitored_objects.data.split(',')
        config.notification_threshold = form.confidence_threshold.data
        flash('Settings saved successfully!', 'success')
        return redirect(url_for('index'))
    if not form.is_submitted():
        form.monitored_objects.data = ','.join(config.monitored_objects)
        form.confidence_threshold.data = config.notification_threshold
    return render_template('settings.html', form=form, available_classes=available_classes)

@app.route('/video_feed')
def video_feed():
    # Check if we're in a production environment (like Render)
    is_production = os.environ.get('RENDER', False)
    
    # Run both detectors and merge results
    def generate_frames():
        while True:
            frame = None
            detected_objects = []
            
            # Get frame from camera or demo mode
            if custom_detector and custom_detector.model_loaded:
                custom_detector._ensure_camera_open()
                # Check if we're in demo mode
                if hasattr(custom_detector, 'demo_mode') and custom_detector.demo_mode:
                    frame = custom_detector.demo_frame.copy()
                    ret = True
                else:
                    ret, frame = custom_detector.cap.read()
            elif coco_detector and coco_detector.model_loaded:
                coco_detector._ensure_camera_open()
                # Check if we're in demo mode
                if hasattr(coco_detector, 'demo_mode') and coco_detector.demo_mode:
                    frame = coco_detector.demo_frame.copy()
                    ret = True
                else:
                    ret, frame = coco_detector.cap.read()
            else:
                break
                
            if not ret or frame is None:
                break
                
            # Run both detectors on the same frame
            frame_custom, detected_custom = (frame, [])
            frame_coco, detected_coco = (frame, [])
            
            if custom_detector and custom_detector.model_loaded:
                frame_custom, detected_custom = custom_detector._process_frame(frame.copy(), config)
            if coco_detector and coco_detector.model_loaded:
                frame_coco, detected_coco = coco_detector._process_frame(frame.copy(), config)
                
            # Overlay both results (custom first, then coco)
            # For simplicity, show custom detections on frame
            # Optionally, you could merge bounding boxes from both
            # Here, just use custom's frame if any custom detection, else coco's
            if detected_custom:
                out_frame = frame_custom
            else:
                out_frame = frame_coco
                
            # Encode and yield
            ret, buffer = cv2.imencode('.jpg', out_frame)
            if not ret:
                continue
                
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            
            # If in demo mode, add a small delay to simulate video
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