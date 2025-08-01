from flask import Flask, render_template, request, jsonify
import os
import threading
import io
import sys
from controles.downloadtiktok import run_tiktok_downloader
from controles.downloadyoutube import run_youtube_downloader
from controles.postautomaticoyoutube import run_youtube_uploader

app = Flask(__name__, static_folder='static')

# Store original stdout and stderr before redirection
original_stdout = sys.stdout
original_stderr = sys.stderr

class Tee:
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()
    def flush(self, *args, **kwargs):
        for f in self.files:
            f.flush()

# Variáveis globais para armazenar o log e o status
log_stream = io.StringIO()
sys.stdout = Tee(original_stdout, log_stream)
sys.stderr = Tee(original_stderr, log_stream)
status = {'running': False, 'log': '', 'message': '', 'error': '', 'downloaded_videos': []}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tiktok')
def tiktok():
    return render_template('tiktok.html')

@app.route('/youtube')
def youtube():
    return render_template('youtube.html')

@app.route('/upload')
def upload():
    return render_template('upload.html')

@app.route('/downloads')
def downloads():
    downloads_dir = os.path.join(app.static_folder, '../downloads')
    videos = []
    if os.path.exists(downloads_dir):
        videos = [f for f in os.listdir(downloads_dir) if f.endswith('.mp4')]
    return render_template('downloads.html', videos=videos)

def run_task(target, *args):
    global status
    status['running'] = True
    status['log'] = ''
    status['message'] = ''
    status['error'] = ''
    status['downloaded_videos'] = [] # Clear previous downloads
    log_stream.truncate(0)
    log_stream.seek(0)
    try:
        result = target(*args)
        if result and isinstance(result, list):
            status['downloaded_videos'] = result
        status['message'] = 'Download concluído com sucesso!'
    except Exception as e:
        status['error'] = f'Ocorreu um erro: {str(e)}'
    finally:
        status['running'] = False

@app.route('/run-tiktok-download', methods=['POST'])
def run_tiktok_download_route():
    hashtags = request.form.get('hashtags')
    quantity = int(request.form.get('quantity'))
    thread = threading.Thread(target=run_task, args=(run_tiktok_downloader, hashtags, quantity))
    thread.start()
    return jsonify({'status': 'started'})

@app.route('/run-youtube-download', methods=['POST'])
def run_youtube_download_route():
    terms = request.form.get('terms')
    quantity = int(request.form.get('quantity'))
    thread = threading.Thread(target=run_task, args=(run_youtube_downloader, terms, quantity))
    thread.start()
    return jsonify({'status': 'started'})

@app.route('/run-upload', methods=['POST'])
def run_upload_route():
    thread = threading.Thread(target=run_task, args=(run_youtube_uploader,))
    thread.start()
    return jsonify({'status': 'started'})

@app.route('/status')
def get_status():
    global status
    status['log'] = log_stream.getvalue()
    return jsonify(status)

if __name__ == '__main__':
    app.run(debug=True)