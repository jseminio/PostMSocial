import os
import pickle
import glob
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError

#  Importante: Instale as dependências necessárias
# Escopo necessário para upload de vídeo
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# Constrói os caminhos absolutos para os arquivos de credenciais e downloads
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, "../credenciais/credentials.json")
CREDENTIALS_PICKLE = os.path.join(BASE_DIR, "../credenciais/youtube_token.pickle")
DOWNLOADS_DIR = os.path.join(BASE_DIR, "../downloads")

def get_authenticated_service():
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

def upload_video(youtube, file_path, title, description="", tags=None, categoryId="22", privacyStatus="private"):
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
        print("\n⚠️ Verifique se a API YouTube Data API v3 está ativada neste link:")
        print("https://console.developers.google.com/apis/api/youtube.googleapis.com/overview")
        print("➡️ Aguarde alguns minutos após ativar antes de tentar novamente.")
        return None
    return response

def main():
    """
    Função principal que automatiza o processo de upload de vídeos para o YouTube.

    Primeiro, obtém um serviço autenticado da API do YouTube. Em seguida, procura por arquivos .mp4
    no diretório de downloads. Para cada vídeo encontrado, ele extrai um título do nome do arquivo
    e chama a função `upload_video` para enviá-lo ao YouTube com configurações padrão.
    """
    youtube = get_authenticated_service()
    video_files = glob.glob(os.path.join(DOWNLOADS_DIR, "*.mp4"))
    if not video_files:
        print("Nenhum vídeo encontrado na pasta de downloads.")
        return
    for video in video_files:
        title = os.path.splitext(os.path.basename(video))[0]
        print(f"\n🚀 Iniciando upload do vídeo: {title}")
        upload_video(
            youtube,
            video,
            title=title,
            description="Upload automático via API",
            tags=["automático", "youtube", "api"],
            categoryId="22",  # 22 = People & Blogs
            privacyStatus="public"  # Altere para 'public' se desejar
        )

if __name__ == "__main__":
    main()
