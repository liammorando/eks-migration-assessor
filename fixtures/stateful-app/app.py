import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, jsonify, request

app = Flask(__name__)

# BAD: Hardcoded secret key
SECRET_KEY = "supersecret123"
app.config["SECRET_KEY"] = SECRET_KEY

# BAD: Hardcoded database host
DB_HOST = "localhost"
DB_PORT = 5432

# BAD: Hardcoded IP address
INTERNAL_SERVICE_IP = "192.168.1.50"

# BAD: AWS-like access key in code
AWS_ACCESS_KEY = "AKIAFAKEFAKEFAKEFAKE"

# BAD: Module-level dict for sessions (not shared across workers)
SESSIONS = {}

# BAD: Local file upload directory
UPLOAD_DIR = "/var/data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# BAD: File logging instead of stdout
log_handler = RotatingFileHandler("/var/log/app.log", maxBytes=10000, backupCount=3)
log_handler.setLevel(logging.INFO)
app.logger.addHandler(log_handler)
app.logger.setLevel(logging.INFO)


@app.route("/healthz")
def healthz():
    return jsonify({"status": "healthy"}), 200


@app.route("/")
def index():
    return jsonify({"message": "Hello from stateful-app"}), 200


@app.route("/upload", methods=["POST"])
def upload():
    # BAD: Write to local filesystem
    file = request.files.get("file")
    if file:
        filepath = os.path.join(UPLOAD_DIR, file.filename)
        file.save(filepath)
        app.logger.info(f"Saved file to {filepath}")
        return jsonify({"path": filepath}), 200
    return jsonify({"error": "No file"}), 400


@app.route("/session", methods=["POST"])
def create_session():
    # BAD: Store session in memory dict
    session_id = os.urandom(16).hex()
    SESSIONS[session_id] = {"user": "test", "data": request.json}
    return jsonify({"session_id": session_id}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
