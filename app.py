from flask import Flask, request, send_file
import yt_dlp
import os

app = Flask(__name__)

@app.route('/')
def home():
    return open("index.html").read()

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data['url']
    quality = data['quality']

    options = {
        'format': f'bestvideo[height<={quality}]+bestaudio/best',
        'outtmpl': 'video.%(ext)s',
        'merge_output_format': 'mp4',
        'quiet': True
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            file = ydl.prepare_filename(info).replace('.webm', '.mp4').replace('.mkv', '.mp4')
            return send_file(file, as_attachment=True)
    except Exception as e:
        return str(e), 500

import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
