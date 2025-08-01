from playwright.sync_api import sync_playwright
import time
import os
import yt_dlp
from datetime import datetime, timedelta

def buscar_links_youtube_24h_mais_vistos(quantidade_de_links_validos=5):
    """
    Busca os links dos vídeos mais visualizados nas últimas 24h no YouTube.
    Parâmetros:
        quantidade_de_links_validos (int): quantidade máxima de links válidos
    Retorna:
        list: [lista de links]
    """
    resultado = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        url = "https://www.youtube.com/results?search_query=&sp=EgQIBRAB"  # Hoje + Ordenar por: Visualizações
        page.goto(url)
        time.sleep(2)
        for _ in range(5):
            page.mouse.wheel(0, 3000)
            time.sleep(1)
        anchors = page.query_selector_all('a#video-title')
        video_links = []
        for elem in anchors:
            link = elem.get_attribute('href')
            if link and '/watch?v=' in link:
                if not link.startswith('http'):
                    link = f"https://www.youtube.com{link}"
                video_links.append(link)
        browser.close()

    # Filtrar vídeos enviados nas últimas 24h e ordenar por visualizações
    links_validos = []
    infos_videos = []
    for link in video_links:
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(link, download=False)
            upload_time = datetime.fromtimestamp(info.get('upload_date', None) and int(datetime.strptime(info['upload_date'], "%Y%m%d").timestamp()))
            now = datetime.now()
            # Se o vídeo foi enviado nas últimas 24 horas
            if (now - upload_time) <= timedelta(hours=24):
                view_count = info.get('view_count', 0)
                infos_videos.append({'link': link, 'view_count': view_count, 'upload_time': upload_time})
        except Exception as e:
            continue

    # Ordena por visualizações (decrescente)
    infos_videos.sort(key=lambda x: x['view_count'], reverse=True)
    for video in infos_videos[:quantidade_de_links_validos]:
        links_validos.append(video['link'])
    return links_validos

def baixar_videos(links):
    """
    Baixa vídeos dos links informados usando yt-dlp na pasta downloads.
    """
    download_dir = os.path.join(os.path.dirname(__file__), 'downloads')
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    ydl_opts = {
        'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
        'quiet': False,
        'noplaylist': True,
        'format': 'mp4/bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
    }
    for link in links:
        print(f"Tentando baixar: {link}")
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])
        except Exception as e:
            print(f"Erro ao baixar {link}: {e}")

def main():
    print("Quantos vídeos mais visualizados nas últimas 24h você deseja baixar?")
    try:
        qtd = int(input().strip())
    except ValueError:
        print("Quantidade inválida. Encerrando.")
        return
    links = buscar_links_youtube_24h_mais_vistos(quantidade_de_links_validos=qtd)
    print("\nLinks encontrados:")
    for link in links:
        print(link)
    if not links:
        print("Nenhum link encontrado ou a página demorou para carregar ou não há vídeos enviados nas últimas 24h.")
    else:
        print(f"\nIniciando download dos vídeos mais visualizados nas últimas 24h...")
        baixar_videos(links)
    print("Encerrando o programa.")

if __name__ == "__main__":
    main()
