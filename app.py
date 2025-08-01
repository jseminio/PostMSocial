from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)

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
    downloads_dir = os.path.join(app.static_folder, 'downloads')
    videos = []
    if os.path.exists(downloads_dir):
        videos = [f for f in os.listdir(downloads_dir) if f.endswith('.mp4')]
    return render_template('downloads.html', videos=videos)

if __name__ == '__main__':
    app.run(debug=True)
