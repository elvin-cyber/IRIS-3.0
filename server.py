"""
IRIS web server
================
This file is NEW. It does not change anything in core/, memory/, or
tools/ — it only imports and calls the existing `respond()` function
exactly the way main.py (the terminal version) already does, and
exposes it over a small local HTTP API so the web HUD (static/) can
talk to IRIS from a browser.

Run:
    python server.py
Then open:
    http://127.0.0.1:5000
"""

from pathlib import Path

import requests
from flask import Flask, jsonify, request, send_from_directory

from core.iris import respond
from memory.manager import get_assistant_info, get_user_name

STATIC_DIR = Path(__file__).parent / "static"
OLLAMA_HEALTH_URL = "http://localhost:11434"

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="")


@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/api/greeting")
def greeting():
    """Same greeting shown by main.py, for the HUD's opening line."""
    info = get_assistant_info()
    return jsonify(
        {
            "user_name": get_user_name() or "there",
            "assistant_name": info.get("name", "IRIS"),
        }
    )


@app.route("/api/health")
def health():
    """Lets the HUD show an ONLINE / OFFLINE badge for the Ollama model."""
    try:
        requests.get(OLLAMA_HEALTH_URL, timeout=2)
        return jsonify({"ollama": "online"})
    except requests.exceptions.RequestException:
        return jsonify({"ollama": "offline"})


@app.route("/api/chat", methods=["POST"])
def chat():
    """Same brain call main.py makes: core.iris.respond(user_input)."""
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "empty message"}), 400
    if message.lower() in {"exit", "quit", "bye"}:
        name = get_user_name() or "there"
        return jsonify({"reply": f"Goodbye, {name}!", "exit": True})
    reply = respond(message)
    return jsonify({"reply": reply, "exit": False})


if __name__ == "__main__":
    print("IRIS web HUD starting at http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
