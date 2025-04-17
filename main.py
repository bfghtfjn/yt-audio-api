import os
import secrets
import threading
from flask import Flask, request, jsonify, send_from_directory
from uuid import uuid4
from pathlib import Path
import yt_dlp
import access_manager
from constants import *

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "YouTube to MP3 API is running!"

@app.route("/yt", methods=["GET"])
def handle_audio_request():
    video_url = request.args.get("url")
    if not video_url:
        return jsonify(error="Missing 'url' parameter in request."), BAD_REQUEST

    filename = f"{uuid4()}.mp3"
    output_path = Path(ABS_DOWNLOADS_PATH) / filename

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': str(output_path),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        }],
        'quiet': True,
        'cookiefile': 'cookies.txt'  # لازم تكون مرفوعة بالملف
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
    except Exception as e:
        return jsonify(error="Download failed", detail=str(e)), INTERNAL_SERVER_ERROR

    return _generate_token_response(filename)

@app.route("/download", methods=["GET"])
def download_audio():
    token = request.args.get("token")
    if not token:
        return jsonify(error="Missing token"), BAD_REQUEST

    if not access_manager.has_access(token):
        return jsonify(error="Invalid token"), UNAUTHORIZED

    if not access_manager.is_valid(token):
        return jsonify(error="Token expired"), REQUEST_TIMEOUT

    try:
        filename = access_manager.get_audio_file(token)
        return send_from_directory(ABS_DOWNLOADS_PATH, filename=filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify(error="File not found"), NOT_FOUND

def _generate_token_response(filename: str):
    token = secrets.token_urlsafe(TOKEN_LENGTH)
    access_manager.add_token(token, filename)
    return jsonify(token=token)

def main():
    token_cleaner_thread = threading.Thread(
        target=access_manager.manage_tokens,
        daemon=True
    )
    token_cleaner_thread.start()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    main()
    app.run(host="0.0.0.0", port=port)
