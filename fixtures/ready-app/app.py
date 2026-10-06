import os
import signal
import sys

from flask import Flask, jsonify

app = Flask(__name__)

# Config from environment variables (12-factor)
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
PORT = int(os.getenv("PORT", "8080"))
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-prod")

app.config["SECRET_KEY"] = SECRET_KEY


@app.route("/healthz")
def healthz():
    return jsonify({"status": "healthy"}), 200


@app.route("/")
def index():
    return jsonify({"message": "Hello from ready-app"}), 200


def handle_shutdown(signum, frame):
    print("SIGTERM received, shutting down gracefully...")
    sys.exit(0)


signal.signal(signal.SIGTERM, handle_shutdown)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
