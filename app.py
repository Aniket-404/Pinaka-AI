import os
from flask import Flask, render_template, redirect, url_for, flash, Response
from flask_socketio import SocketIO
from app.forms import NotificationForm
from app.utils.object_detector import ObjectDetector
from app.utils.config import Config
from dotenv import load_dotenv
import cv2

# Load environment variables
load_dotenv()

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

try:
    print(f"Attempting to load custom model: {custom_model_path}")
    custom_detector = ObjectDetector(model_path=custom_model_path, socketio=socketio)
    if custom_detector.model_loaded:
        print(f"Custom model loaded with classes: {list(custom_detector.model.names.values())}")
    else:
        print("Custom model failed to load.")
except Exception as e:
    print(f"Error loading custom model: {e}")

try:
    print(f"Attempting to load COCO model: {coco_model_path}")
    coco_detector = ObjectDetector(model_path=coco_model_path, socketio=socketio)
    if coco_detector.model_loaded:
        print(f"COCO model loaded with classes: {list(coco_detector.model.names.values())}")
    else:
        print("COCO model failed to load.")
except Exception as e:
    print(f"Error loading COCO model: {e}")

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
    # Run both detectors and merge results
    def generate_frames():
        while True:
            frame = None
            detected_objects = []
            # Get frame from camera (use custom_detector's camera logic)
            if custom_detector and custom_detector.model_loaded:
                custom_detector._ensure_camera_open()
                ret, frame = custom_detector.cap.read()
            elif coco_detector and coco_detector.model_loaded:
                coco_detector._ensure_camera_open()
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
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, debug=True)