from flask import Flask, request, send_file, abort, after_this_request
import subprocess, uuid, os, time, re
from urllib.parse import urlparse

app = Flask(__name__)
LAST_REQUEST = {}
TEMP_FILES = set()

def cleanup_temp_files():
    """Nettoyer les fichiers temporaires"""
    for filepath in list(TEMP_FILES):
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                TEMP_FILES.remove(filepath)
        except:
            pass

@app.route("/")
def home():
    return "Backend OK 🚀"

@app.route("/download")
def download():
    url = request.args.get("url")
    if not url:
        abort(400, "URL manquant")

    # Validation basique de l'URL
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            abort(400, "URL invalide")
    except:
        abort(400, "URL invalide")

    ip = request.remote_addr
    now = time.time()

    # 🔒 Limit 1 requête / 20s per IP
    if ip in LAST_REQUEST and now - LAST_REQUEST[ip] < 20:
        abort(429, "Trop de requêtes, patientez 20s")
    LAST_REQUEST[ip] = now

    # Nettoyer les vieilles entrées (plus de 1 heure)
    for old_ip in list(LAST_REQUEST.keys()):
        if now - LAST_REQUEST[old_ip] > 3600:
            del LAST_REQUEST[old_ip]

    # Validation TikTok
    if not re.search(r'(tiktok\.com|tiktok\.com/@)', url, re.IGNORECASE):
        abort(400, "Seuls les liens TikTok sont autorisés")

    filename = f"{uuid.uuid4()}.mp4"
    filepath = f"/tmp/{filename}"

    try:
        # Téléchargement avec yt-dlp
        cmd = [
            "yt-dlp",
            "-f", "best[ext=mp4]/best",
            "--no-check-certificate",
            "--socket-timeout", "10",
            "--retries", "3",
            "--max-filesize", "50M",  # Limite de taille
            "-o", filepath,
            url
        ]
        
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=45  # 45s max
        )
        
        if process.returncode != 0:
            raise Exception(f"yt-dlp failed: {process.stderr}")
            
    except subprocess.TimeoutExpired:
        abort(504, "Timeout: vidéo trop longue ou non accessible")
    except Exception as e:
        # Nettoyage en cas d'erreur
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass
        abort(500, f"Erreur de téléchargement: {str(e)[:100]}")

    if not os.path.exists(filepath):
        abort(500, "Fichier introuvable après téléchargement")

    # Vérifier la taille du fichier
    file_size = os.path.getsize(filepath)
    if file_size == 0:
        os.remove(filepath)
        abort(500, "Fichier vide")
    
    if file_size > 50 * 1024 * 1024:  # 50MB max
        os.remove(filepath)
        abort(413, "Vidéo trop volumineuse (>50MB)")

    # Ajouter à la liste des fichiers temporaires
    TEMP_FILES.add(filepath)

    @after_this_request
    def remove_file(response):
        """Nettoyer le fichier après envoi"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                TEMP_FILES.discard(filepath)
        except Exception as e:
            app.logger.error(f"Error removing file {filepath}: {e}")
        return response

    try:
        return send_file(
            filepath,
            as_attachment=True,
            download_name="tiktok_video.mp4",
            mimetype="video/mp4",
            max_age=0  # Pas de cache
        )
    except Exception as e:
        # Nettoyage en cas d'erreur d'envoi
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                TEMP_FILES.discard(filepath)
            except:
                pass
        abort(500, f"Erreur d'envoi: {str(e)[:100]}")

@app.errorhandler(404)
def not_found(e):
    return "Route non trouvée", 404

@app.errorhandler(500)
def server_error(e):
    return "Erreur serveur interne", 500

if __name__ == "__main__":
    # Nettoyer au démarrage
    cleanup_temp_files()
    
    port = int(os.environ.get("PORT", 8080))
    # Désactiver le debug en production
    debug = os.environ.get("DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
