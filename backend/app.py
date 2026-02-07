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
    if not url:
        abort(400, "URL manke")

    ip = request.remote_addr
    now = time.time()

    # 🔒 Limit 1 requête / 20s per IP
    if ip in LAST_REQUEST and now - LAST_REQUEST[ip] < 20:
        abort(429, "Trop de requêtes, patiente 20s")
    LAST_REQUEST[ip] = now

    if "tiktok.com" not in url:
        abort(400, "Seuls les liens TikTok sont autorisés")

    filename = f"{uuid.uuid4()}.mp4"
    filepath = f"/tmp/{filename}"

    try:
        # Télécharge video MP4 / fallback si MP4 pa disponib
        subprocess.run(
            ["yt-dlp", "-f", "best[ext=mp4]/best", "--no-check-certificate", "-o", filepath, url],
            check=True,
            timeout=50  # 50s max pou free dyno
        )
    except subprocess.TimeoutExpired:
        abort(504, "Download timeout, vidéo trop longue")
    except Exception as e:
        abort(500, f"yt-dlp error: {e}")

    if not os.path.exists(filepath):
        abort(500, "Fichier introuvable")

    return send_file(
        filepath,
        as_attachment=True,
        download_name="video.mp4",
        mimetype="video/mp4"
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
