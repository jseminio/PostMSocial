from playwright.sync_api import sync_playwright
import time
import os
import yt_dlp

def buscar_links_youtube(termos, quantidade_de_links_validos=5):
    """
    Busca links de vídeos públicos do YouTube para cada termo informado.
    """
    resultado = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for termo in termos:
            print(f"\nBuscando vídeos para: {termo}")
            url = f"https://www.youtube.com/results?search_query={termo}"
            page.goto(url)
            time.sleep(2)
            for _ in range(5):
                page.mouse.wheel(0, 3000)
                time.sleep(1)
            video_links = set()
            anchors = page.query_selector_all('a#video-title')
            for elem in anchors:
                link = elem.get_attribute('href')
                if link and '/watch?v=' in link:
                    if link.startswith('http'):
                        video_links.add(link)
                    else:
                        video_links.add(f"https://www.youtube.com{link}")
                if len(video_links) >= quantidade_de_links_validos:
                    break
            resultado[termo] = list(video_links)[:quantidade_de_links_validos]
        browser.close()
    return resultado

def baixar_videos(links):
    """
    Baixa vídeos dos links informados usando yt-dlp na pasta downloads.
    Retorna uma lista de dicionários com informações sobre cada download.
    """
    download_dir = os.path.join(os.path.dirname(__file__), '../downloads')
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    downloaded_videos_info = []

    for link in links:
        video_info = {
            'url': link,
            'title': 'Desconhecido',
            'filepath': 'N/A',
            'status': 'Iniciando'
        }
        try:
            # Get video info without downloading
            ydl_opts_info = {
                'quiet': True,
                'noplaylist': True,
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
            }
            with yt_dlp.YoutubeDL(ydl_opts_info) as ydl_info:
                info_dict = ydl_info.extract_info(link, download=False)
                video_info['title'] = info_dict.get('title', 'Desconhecido')
                # Construct expected filepath
                # yt-dlp automatically adds extension, so we just need the base name
                expected_filename_base = ydl_info.prepare_filename(info_dict).split(os.sep)[-1]
                video_info['filepath'] = os.path.join(download_dir, expected_filename_base)

            ydl_opts_download = {
                'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
                'quiet': False,
                'noplaylist': True,
                'format': 'mp4/bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
            }
            print(f"Tentando baixar: {link}")
            with yt_dlp.YoutubeDL(ydl_opts_download) as ydl_download:
                ydl_download.download([link])
                video_info['status'] = 'Concluído'
        except Exception as e:
            print(f"Erro ao baixar {link}: {e}")
            video_info['status'] = f'Erro: {str(e)}'
        finally:
            downloaded_videos_info.append(video_info)
    return downloaded_videos_info

def run_youtube_downloader(terms_input, quantity):
    """
    Executa o processo completo de download de vídeos do YouTube com base nos parâmetros fornecidos.
    Retorna uma lista de dicionários com informações sobre os vídeos baixados.
    """
    print(f"Buscando vídeos para os termos: {terms_input}")
    termos_escolhidos = [t.strip().replace('#', '') for t in terms_input.split(',') if t.strip()]
    if not termos_escolhidos:
        print("Nenhum termo válido fornecido.")
        return [] # Return empty list if no terms

    links_por_termo = buscar_links_youtube(termos_escolhidos, quantidade_de_links_validos=quantity)
    all_downloaded_videos = []
    for termo, links in links_por_termo.items():
        print(f"\nLinks encontrados para '{termo}':")
        for link in links:
            print(link)
        if not links:
            print("Nenhum link encontrado ou a página demorou para carregar.")
        else:
            print(f"\nIniciando download dos vídeos para '{termo}'...")
            download_results = baixar_videos(links)
            all_downloaded_videos.extend(download_results)
    print("\nProcesso de download do YouTube concluído.")
    return all_downloaded_videos

if __name__ == '__main__':
    # Lógica interativa para execução direta do script
    print("\nDigite os termos (hashtags ou palavras) para buscar vídeos no YouTube, separados por vírgula (ex: futebol,tecnologia):")
    termos_input = input().strip()
    print("Quantos links válidos por termo você deseja baixar?")
    try:
        qtd = int(input().strip())
    except ValueError:
        qtd = 5
    run_youtube_downloader(termos_input, qtd)

