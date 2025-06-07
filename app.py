import os
from flask import Flask, render_template, redirect, url_for, flash, Response
from flask_socketio import SocketIO
from app.forms import NotificationForm
from app.utils.object_detector import ObjectDetector
from app.utils.config import Config
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Flask app with correct template folder
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'app', 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'app', 'static'))
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
socketio = SocketIO(app)

# Try to download the YOLOv8n model if it doesn't exist
model_path = "custom_yolo_100epochs_best.pt"
if not os.path.exists(model_path):
    try:
        import urllib.request
        print(f"Manually downloading {model_path}...")
        url = "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt"
        urllib.request.urlretrieve(url, model_path)
        print(f"Successfully downloaded {model_path}")
    except Exception as e:
        print(f"Failed to download model: {e}")

# Initialize the object detector with the standard YOLOv8n model
try:
    print(f"Attempting to load model: {model_path}")
    object_detector = ObjectDetector(model_path=model_path, socketio=socketio)
    if not object_detector.model_loaded:
        print("Standard model failed to load. Using fallback detection.")
        object_detector = ObjectDetector(model_path="", socketio=socketio, use_fallback=True)
except Exception as e:
    print(f"Error initializing object detector: {e}")
    print("Using fallback detection.")
    object_detector = ObjectDetector(model_path="", socketio=socketio, use_fallback=True)

# Config for detection settings
config = Config()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    form = NotificationForm()
    
    # Get available classes if model is loaded
    available_classes = []
    if object_detector.model_loaded and hasattr(object_detector.model, 'names'):
        available_classes = list(object_detector.model.names.values())
    
    # Always include Movement for fallback detection
    if "Movement" not in available_classes:
        available_classes.append("Movement")
    
    if form.validate_on_submit():
        config.monitored_objects = form.monitored_objects.data.split(',')
        config.notification_threshold = form.confidence_threshold.data
        flash('Settings saved successfully!', 'success')
        return redirect(url_for('index'))
        
    # Pre-populate form with current settings
    if not form.is_submitted():
        form.monitored_objects.data = ','.join(config.monitored_objects)
        form.confidence_threshold.data = config.notification_threshold
        
    return render_template('settings.html', form=form, available_classes=available_classes)

@app.route('/video_feed')
def video_feed():
    return Response(
        object_detector.generate_frames(config),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, debug=True) 