from flask import Flask, request, send_file, abort, after_this_request
import subprocess, uuid, os, time, requests

app = Flask(__name__)
LAST_REQUEST = {}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; Mobile)",
    "Referer": "https://www.tiktok.com/"
}

def get_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr)

def resolve_url(url):
    r = requests.get(url, headers=HEADERS, allow_redirects=True, timeout=10)
    return r.url

@app.route("/")
def home():
    return "SSSTIK Style Backend 🚀 (MP3 + 720p)"

@app.route("/download")
def download():
    url = request.args.get("url")
    dtype = request.args.get("type", "video")   # video | mp3

    if not url or "tiktok" not in url:
        abort(400, "Lien TikTok requis")

    ip = get_ip()
    now = time.time()
    if ip in LAST_REQUEST and now - LAST_REQUEST[ip] < 15:
        abort(429, "Attendez 15 secondes")
    LAST_REQUEST[ip] = now

    try:
        resolved = resolve_url(url)
    except:
        abort(400, "Lien invalide")

    uid = str(uuid.uuid4())

    # 🎵 MP3
    if dtype == "mp3":
        filepath = f"/tmp/{uid}.mp3"
        cmd = [
            "yt-dlp",
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "5",
            "--no-playlist",
            "-o", filepath,
            resolved
        ]

    # 🎬 VIDEO 720p
    else:
        filepath = f"/tmp/{uid}.mp4"
        cmd = [
            "yt-dlp",
            "-f", "bv*[height<=720][ext=mp4]/b[ext=mp4]",
            "--no-playlist",
            "--user-agent", HEADERS["User-Agent"],
            "-o", filepath,
            resolved
        ]

    try:
        subprocess.run(cmd, check=True, timeout=50)
    except subprocess.TimeoutExpired:
        abort(504, "Timeout téléchargement")
    except:
        abort(500, "Erreur téléchargement")

    if not os.path.exists(filepath):
        abort(500, "Fichier non généré")

    @after_this_request
    def cleanup(response):
        try:
            os.remove(filepath)
        except:
            pass
        return response

    return send_file(
        filepath,
        as_attachment=True,
        download_name=os.path.basename(filepath),
        mimetype="application/octet-stream"
    )
