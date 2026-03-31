from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import time

app = Flask(__name__)
CORS(app)

# Cache to store results for 10 minutes
cache = {}


@app.route('/api/get_video', methods=['POST'])
def get_video():
    data = request.json
    video_url = data.get('url')

    if not video_url:
        return jsonify({"error": "URL is required"}), 400

    # Return from cache if available
    if video_url in cache and (time.time() - cache[video_url]['time'] < 600):
        return jsonify(cache[video_url]['data'])

    try:
        # Configuration for Video and Audio
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

            # Extract Audio link (if available, else fallback to video)
            formats = info.get('formats', [])
            audio_url = info.get('url')  # Default
            for f in formats:
                if f.get('vcodec') == 'none':  # This is an audio-only stream
                    audio_url = f.get('url')
                    break

            result = {
                "title": info.get('title', 'Social Media File'),
                "download_url": info.get('url'),
                "audio_url": audio_url,
                "thumbnail": info.get('thumbnail'),
                "source": info.get('extractor_key')
            }

            # Save to cache
            cache[video_url] = {'data': result, 'time': time.time()}

            return jsonify(result)

    except Exception as e:
        return jsonify({
            "error":
            "Could not fetch data. Link might be private or unsupported."
        }), 500


# Vercel requirement
def handler(environ, start_response):
    return app(environ, start_response)
