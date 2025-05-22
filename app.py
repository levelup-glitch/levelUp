
from flask import Flask, request, send_file, jsonify, session
from flask_cors import CORS
import yt_dlp
import os
import json
from uuid import uuid4

# Write the cookie file if injected via env var
if not os.path.exists("cookies.txt") and os.environ.get("COOKIES_TEXT"):
    with open("cookies.txt", "w") as f:
        f.write(os.environ["COOKIES_TEXT"])

app = Flask(__name__)
app.secret_key = os.urandom(24)  # secret key for session
CORS(app)

# Return unique history file for each user
def get_history_file():
    if 'uid' not in session:
        session['uid'] = str(uuid4())
    return f"history_{session['uid']}.json"

@app.route('/')
def home():
    return open("index.html").read()

@app.route('/formats', methods=['POST'])
def get_formats():
    data = request.get_json()
    url = data['url']
    ydl_opts = {'quiet': True}

    if os.path.exists("cookies.txt"):
        ydl_opts['cookiefile'] = 'cookies.txt'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = [
                {
                    "format_id": f['format_id'],
                    "resolution": f.get('format_note') or f.get('height'),
                    "filesize": f.get('filesize') or 0,
                    "ext": f['ext']
                }
                for f in info['formats']
                if f.get('vcodec') != 'none' and f.get('filesize')
            ]
            return jsonify(formats)
    except Exception as e:
        return f"❌ Error: {str(e)}", 500

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data['url']
    quality = data['quality']
    output_file = 'video.%(ext)s'

    ydl_opts = {
        'format': quality,
        'outtmpl': output_file,
        'merge_output_format': 'mp4',
        'quiet': True,
    }

    if os.path.exists("cookies.txt"):
        ydl_opts['cookiefile'] = 'cookies.txt'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info).replace('.webm', '.mp4').replace('.mkv', '.mp4')

            # Save to per-user history
            history_file = get_history_file()
            history = []

            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    history = json.load(f)

            history.append({
                "title": info.get("title"),
                "resolution": quality,
                "size_MB": round(os.path.getsize(filename) / 1024 / 1024, 2)
            })

            with open(history_file, 'w') as f:
                json.dump(history[-20:], f)

            return send_file(filename, as_attachment=True)
    except Exception as e:
        return f"❌ Error: {str(e)}", 500

@app.route('/history')
def get_history():
    history_file = get_history_file()
    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            return jsonify(json.load(f))
    return jsonify([])

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
