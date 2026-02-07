from flask import Flask, request, jsonify, send_file, abort, after_this_request
import requests, subprocess, uuid, os, time, re

app = Flask(__name__)
LAST = {}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; Mobile)",
    "Accept": "*/*",
    "Referer": "https://www.tiktok.com/"
}

def get_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr)

def resolve_tiktok(url):
    r = requests.get(url, headers=HEADERS, allow_redirects=True, timeout=10)
    return r.url

@app.route("/")
def home():
    return "SSSTIK.IO Compatible Backend 🚀"

@app.route("/download")
def download():
    url = request.args.get("url")
    if not url:
        abort(400, "URL requise")

    if "tiktok" not in url:
        abort(400, "Lien TikTok seulement")

    ip = get_ip()
    now = time.time()
    if ip in LAST and now - LAST[ip] < 15:
        abort(429, "Attendez 15 secondes")
    LAST[ip] = now

    try:
        resolved = resolve_tiktok(url)
    except:
        abort(400, "Impossible de résoudre le lien")

    filename = f"{uuid.uuid4()}.mp4"
    path = f"/tmp/{filename}"

    try:
        subprocess.run([
            "yt-dlp",
            "--no-playlist",
            "--extractor-args", "tiktok:api_hostname=api16-normal-c-useast1a.tiktokv.com",
            "--user-agent", HEADERS["User-Agent"],
            "-f", "bestvideo+bestaudio/best",
            "--merge-output-format", "mp4",
            "-o", path,
            resolved
        ], check=True, timeout=60)
    except subprocess.TimeoutExpired:
        abort(504, "Timeout")
    except:
        abort(500, "Erreur TikTok extractor")

    if not os.path.exists(path):
        abort(500, "Fichier non généré")

    @after_this_request
    def cleanup(response):
        try:
            os.remove(path)
        except:
            pass
        return response

    return send_file(
        path,
        as_attachment=True,
        download_name="tiktok_no_watermark.mp4",
        mimetype="video/mp4"
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
