from flask import Flask, request, send_file, jsonify
import yt_dlp
import os
import json

app = Flask(__name__)
HISTORY_FILE = 'history.json'

# Ensure history file exists
if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, 'w') as f:
        json.dump([], f)

@app.route('/')
def home():
    return open("index.html").read()

@app.route('/formats', methods=['POST'])
def get_formats():
    data = request.get_json()
    url = data['url']
    ydl_opts = {'quiet': True}

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
        'format': f'bestvideo[height<={quality}]+bestaudio/best',
        'outtmpl': output_file,
        'merge_output_format': 'mp4',
        'quiet': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info).replace('.webm', '.mp4').replace('.mkv', '.mp4')

            # Add to history
            with open(HISTORY_FILE, 'r') as f:
                history = json.load(f)
            history.append({
                "title": info.get("title"),
                "resolution": quality,
                "size_MB": round(os.path.getsize(filename)/1024/1024, 2)
            })
            with open(HISTORY_FILE, 'w') as f:
                json.dump(history[-20:], f)  # Limit to last 20

            return send_file(filename, as_attachment=True)
    except Exception as e:
        return f"❌ Error: {str(e)}", 500

@app.route('/history')
def get_history():
    with open(HISTORY_FILE, 'r') as f:
        return jsonify(json.load(f))

import os
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
