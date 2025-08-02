from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import os
import threading
import io
import sys
from controles.downloadtiktok import run_tiktok_downloader
from controles.downloadyoutube import run_youtube_downloader
from controles.postautomaticoyoutube import run_youtube_uploader
# Importe a função principal do seu script de processamento de vídeo.
# Certifique-se de que o arquivo 'processador_video.py' está na pasta raiz do projeto.
from controles.processador_video import process_video_from_url as processar_video


app = Flask(__name__, static_folder='static')
app.secret_key = 'uma-chave-secreta-muito-segura' # Necessário para usar flash messages

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

@app.route('/cortes')
def cortes():
    downloads_dir = os.path.join(app.static_folder, '../downloads')
    videos_data = []
    if os.path.exists(downloads_dir):
        # Cria uma lista de dicionários para mapear o nome original para um nome seguro para URL
        all_files = [f for f in os.listdir(downloads_dir) if f.endswith('.mp4')]
        for original_filename in all_files:
            # Substitui espaços por hífens para a URL
            safe_filename = original_filename.replace(' ', '-')
            videos_data.append({
                'original': original_filename,
                'safe': safe_filename
            })

    return render_template('cortes.html', videos=videos_data)

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

# A rota agora aceita GET e recebe o nome do arquivo pela URL
@app.route('/gerar_cortes/<path:filename>')
def gerar_cortes(filename):
    """
    Esta rota recebe o nome de um arquivo de vídeo, realiza o processo de corte
    e redireciona o usuário de volta para a página de cortes.
    """
    downloads_dir = os.path.join(app.static_folder, '../downloads')
    original_filename = None

    # Encontra o nome do arquivo original correspondente ao nome seguro da URL
    for f in os.listdir(downloads_dir):
        if f.endswith('.mp4') and f.replace(' ', '-') == filename:
            original_filename = f
            break

    if not original_filename:
        flash(f'Erro: Vídeo {filename} não encontrado.', 'error')
        return redirect(url_for('cortes'))

    video_path = os.path.join(downloads_dir, original_filename)

    try:
        # Chama a função do seu script, passando o caminho completo do vídeo
        print(f"Iniciando processo de corte para: {video_path}")
        processar_video(video_path)
        flash(f'Vídeo "{original_filename}" processado e cortes gerados com sucesso!', 'success')

    except Exception as e:
        # Captura qualquer erro que possa ocorrer durante o processamento
        print(f"Ocorreu um erro ao processar o vídeo {original_filename}: {e}")
        flash(f'Ocorreu um erro ao processar o vídeo: {str(e)}', 'error')

    return redirect(url_for('cortes'))

if __name__ == '__main__':
    app.run(debug=True)