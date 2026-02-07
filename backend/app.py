from flask import Flask, request, send_file, abort
import subprocess, uuid, os, time

app = Flask(__name__)

LAST_REQUEST = {}

@app.route("/")
def home():
    return "Backend OK 🚀"

@app.route("/download")
def download():
    url = request.args.get("url")
    ip = request.remote_addr
    now = time.time()

    # 🔒 LIMIT: 1 requête / 20 secondes
    if ip in LAST_REQUEST and now - LAST_REQUEST[ip] < 20:
        abort(429, "Trop de requêtes, patiente 20s")

    LAST_REQUEST[ip] = now

    # 🎯 TikTok ONLY
    if "tiktok.com" not in url:
        abort(400, "Seuls les liens TikTok sont autorisés")

    filename = f"{uuid.uuid
