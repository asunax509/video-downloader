from flask import Flask, request, jsonify
import subprocess
import os
import uuid

app = Flask(__name__)

@app.route("/download", methods=["GET"])
def download():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "URL manke"}), 400

    filename = f"{uuid.uuid4()}.mp4"
    filepath = f"/tmp/{filename}"

    try:
        subprocess.run(
            ["yt-dlp", "-f", "mp4", "-o", filepath, url],
            check=True
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "status": "ok",
        "file": filename
    })

@app.route("/")
def home():
    return "Backend OK 🚀"
