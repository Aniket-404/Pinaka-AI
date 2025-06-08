# Simple entry point for running the application
from app import app, socketio

if __name__ == '__main__':
    socketio.run(app, debug=True)
