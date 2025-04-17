import os
from flask import Flask, request, jsonify, send_from_directory
from uuid import uuid4
from pathlib import Path
import yt_dlp

# ثابت للمجلد اللي تنحفظ بيه الملفات
ABS_DOWNLOADS_PATH = "./downloads"
os.makedirs(ABS_DOWNLOADS_PATH, exist_ok=True)

app = Flask(__name__)

@app.route("/")
def home():
    return "YouTube to MP3 API is running!"

@app.route("/convert", methods=["GET"])
def handle_audio_request():
    video_url = request.args.get("url")
    if not video_url:
        return jsonify(error="Missing 'url' parameter in request."), 400

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
        'cookiefile': 'cookies.txt'  # احذف هذا السطر إذا ما تستخدم كوكيز
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
    except Exception as e:
        return jsonify(error="Failed to download audio", detail=str(e)), 500

    return jsonify(link=f"/download/{filename}")

@app.route("/download/<filename>", methods=["GET"])
def download_audio(filename):
    try:
        return send_from_directory(ABS_DOWNLOADS_PATH, filename=filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify(error="File not found"), 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
