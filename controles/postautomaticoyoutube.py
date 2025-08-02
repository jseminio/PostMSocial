import os
import pickle
import glob
import shutil
from datetime import datetime
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError

# Constrói os caminhos absolutos para os arquivos de credenciais e downloads
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, "../credenciais/credentials.json")
CREDENTIALS_PICKLE = os.path.join(BASE_DIR, "../credenciais/youtube_token.pickle")
DOWNLOADS_DIR = os.path.join(BASE_DIR, "../downloads")
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_authenticated_service():
    """
    Autentica o usuário com a API do YouTube usando OAuth 2.0.
    """
    creds = None
    if os.path.exists(CREDENTIALS_PICKLE):
        with open(CREDENTIALS_PICKLE, "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(CREDENTIALS_PICKLE, "wb") as token:
            pickle.dump(creds, token)
    return build("youtube", "v3", credentials=creds)

def upload_video(youtube, file_path, title, description="", tags=None, categoryId="22", privacyStatus="public"):
    """
    Faz o upload de um arquivo de vídeo para o YouTube.
    """
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or [],
            "categoryId": categoryId
        },
        "status": {
            "privacyStatus": privacyStatus
        }
    }
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )
    response = None
    try:
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Enviando {int(status.progress() * 100)}% do vídeo '{title}'...")
        print(f"✅ Upload finalizado: {title}")
    except HttpError as e:
        print(f"❌ Erro durante o upload do vídeo '{title}':\n{e}")
        return None
    return response

# Define o diretório base para vídeos enviados
UPLOADED_DIR = os.path.join(BASE_DIR, "../enviado")

def move_uploaded_video(file_path, social_network):
    """
    Move o vídeo enviado para a pasta de destino com a estrutura de data.
    """
    today = datetime.now()
    date_path = today.strftime("%d%m%Y") # Formato DDMMYYYY
    
    target_dir = os.path.join(UPLOADED_DIR, date_path, social_network)
    os.makedirs(target_dir, exist_ok=True)
    
    file_name = os.path.basename(file_path)
    target_path = os.path.join(target_dir, file_name)
    
    try:
        shutil.move(file_path, target_path)
        print(f"✅ Vídeo movido para: {target_path}")
    except Exception as e:
        print(f"❌ Erro ao mover o vídeo {file_name}: {e}")

def run_youtube_uploader():
    """
    Executa o processo de upload de todos os vídeos na pasta de downloads para o YouTube.
    """
    print("Iniciando processo de upload para o YouTube...")
    youtube = get_authenticated_service()
    video_files = glob.glob(os.path.join(DOWNLOADS_DIR, "*.mp4"))
    if not video_files:
        print("Nenhum vídeo encontrado na pasta de downloads.")
        return

    for video in video_files:
        title = os.path.splitext(os.path.basename(video))[0]
        print(f"\n🚀 Iniciando upload do vídeo: {title}")
        response = upload_video(
            youtube,
            video,
            title=title,
            description="Upload automático via API",
            tags=["automático", "youtube", "api"],
            categoryId="22",
            privacyStatus="public"
        )
        if response: # Only move if upload was successful
            move_uploaded_video(video, "youtube")
    print("\nProcesso de upload concluído.")

if __name__ == '__main__':
    run_youtube_uploader()
