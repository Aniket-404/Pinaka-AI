# Pinaka-AI: YOLOv8 Custom Object Detection System

## Overview
Pinaka-AI is a production-ready, minimal, and clear object detection system using YOLOv8 and Flask. It supports real-time detection, custom datasets, and a unified training/deployment pipeline.

## Project Structure
- `app.py` — Flask web server for real-time detection and notifications
- `app/` — Web templates, static files, forms, and utility modules
- `models/` — YOLO model weights and config files
- `custom_dataset/` — Images and labels for training/validation
- `backup_models/` — Backup of best model weights
- `training/` — Training configs, logs, results, and pipeline scripts
    - `scripts/master_script.py` — Single entry-point for full training pipeline
- `docs/` — Documentation and guides

> **Note:**
> For full portability, all configuration files (such as `models/custom_dataset.yaml` and `training/config.yaml`) should use only relative paths (e.g., `path: .`). Do **not** use absolute paths. This ensures the project works on any machine after cloning.

## Installation
1. **Clone the repository:**
   ```bash
   git clone <your_repo_url>
   cd pinaka-ai
   ```
2. **(Optional) Set up a virtual environment:**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Workflow
### 1. Training Pipeline
- Run the full pipeline (prepare, train, evaluate, deploy):
  ```bash
  python training/scripts/master_script.py
  ```
- For stepwise control, use:
  ```bash
  python training/scripts/master_script.py --step train
  python training/scripts/master_script.py --step test
  # etc.
  ```
- Quick test run (10 epochs):
  ```bash
  python training/scripts/master_script.py --quick
  ```

### 2. Running the Web App Locally
- Start the Flask server:
  ```bash
  python app.py
  ```
- Open your browser at [http://localhost:5000](http://localhost:5000)

### 3. Deployment on Render
- This project is configured for deployment on Render.com
- Files for deployment:
  - `Procfile`: Specifies the command to run the application
  - `runtime.txt`: Specifies the Python version
  - `render.yaml`: Configuration for Render deployment
  - `wsgi.py`: Entry point for gunicorn

- To deploy on Render:
  1. Push this repository to GitHub
  2. Create a new Web Service on Render
  3. Connect your GitHub repository
  4. Render will automatically detect the configuration
  5. Click "Create Web Service"

- Note: The deployed version will run in demo mode without camera access, as web servers don't have access to physical cameras. For full functionality with camera access, run the application locally.

## Notes
- Place your YOLO model weights in the `models/` directory.
- The `custom_dataset/` folder should be organized as per YOLOv8 requirements.
- All configuration is handled via `training/config.yaml` and environment variables in `.env`.

## SMS Notifications
Pinaka-AI now supports SMS notifications when objects are detected. To enable this feature:

1. **Set up a Twilio account:**
   - Sign up at [Twilio](https://www.twilio.com/)
   - Purchase a phone number
   - Get your Account SID and Auth Token

2. **Configure your environment variables:**
   - Copy `.env.example` to `.env`
   - Fill in your Twilio credentials:
     ```
     TWILIO_ACCOUNT_SID=your_account_sid
     TWILIO_AUTH_TOKEN=your_auth_token
     TWILIO_FROM_NUMBER=your_twilio_phone_number
     TWILIO_TO_NUMBER=your_phone_number
     ```

3. **Enable SMS notifications in the application:**
   - Go to Settings page
   - Check "Enable SMS Notifications"
   - Specify which objects should trigger SMS alerts
   - Set the cooldown period between notifications

SMS notifications include object type, detection confidence, timestamp, and object coordinates.

## License
MIT License. See `LICENSE` for details.
