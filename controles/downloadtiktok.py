from playwright.sync_api import sync_playwright
import time
import os
import yt_dlp

def get_trending_hashtags_with_views():
    """
    Navega até a página de tendências do TikTok para extrair as hashtags em alta e o número de visualizações.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.tiktok.com/discover")
        page.wait_for_selector('a[href^="/tag/"]', timeout=15000)
        time.sleep(2)
        hashtag_elements = page.query_selector_all('a[href^="/tag/"]')
        hashtags = []
        for elem in hashtag_elements:
            tag = elem.inner_text()
            if tag.startswith("#"):
                parent = elem.evaluate_handle('node => node.parentElement')
                views = None
                if parent:
                    siblings = parent.query_selector_all('span, div')
                    for sib in siblings:
                        sib_text = sib.inner_text().strip()
                        if (sib_text and ("visualiza" in sib_text.lower() or "views" in sib_text.lower() or "M" in sib_text or "K" in sib_text)) and not sib_text.startswith("#"):
                            views = sib_text
                            break
                hashtags.append({
                    'hashtag': tag,
                    'visualizacoes': views if views else 'N/A'
                })
        browser.close()
        return hashtags

def obter_links_hashtag(hashtags, quantidade_de_links_validos=5):
    """
    Busca links de vídeos públicos autorizados para download em cada hashtag informada.
    """
    resultado = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for hashtag in hashtags:
            url = f"https://www.tiktok.com/tag/{hashtag}"
            page.goto(url)
            try:
                page.wait_for_selector('a[href^="/video/"]', timeout=25000)
            except Exception:
                resultado[hashtag] = []
                continue
            for _ in range(10):
                page.mouse.wheel(0, 3000)
                time.sleep(1.5)
            video_links = set()
            anchors = page.query_selector_all('a')
            for elem in anchors:
                link = elem.get_attribute('href')
                if link and ('/video/' in link):
                    if link.startswith('http'):
                        video_links.add(link)
                    else:
                        video_links.add(f"https://www.tiktok.com{link}")
                if len(video_links) >= quantidade_de_links_validos:
                    break
            resultado[hashtag] = list(video_links)[:quantidade_de_links_validos]
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

def run_tiktok_downloader(hashtags_input, quantity):
    """
    Executa o processo completo de download de vídeos do TikTok com base nos parâmetros fornecidos.
    Retorna uma lista de dicionários com informações sobre os vídeos baixados.
    """
    print(f"Buscando vídeos para as hashtags: {hashtags_input}")
    hashtags_escolhidas = [h.strip().replace('#', '').lower() for h in hashtags_input.split(',')]
    if not hashtags_escolhidas:
        print("Nenhuma hashtag válida fornecida.")
        return [] # Return empty list if no hashtags

    links_por_hashtag = obter_links_hashtag(hashtags_escolhidas, quantidade_de_links_validos=quantity)
    all_downloaded_videos = []
    for hashtag, links in links_por_hashtag.items():
        print(f"\nLinks autorizados para download em #{hashtag}:")
        for link in links:
            print(link)
        if not links:
            print("Nenhum link autorizado encontrado ou a página demorou para carregar.")
        else:
            print(f"\nIniciando download dos vídeos da hashtag #{hashtag}...")
            download_results = baixar_videos(links)
            all_downloaded_videos.extend(download_results)
    print("\nProcesso de download do TikTok concluído.")
    return all_downloaded_videos

if __name__ == '__main__':
    # Lógica interativa para execução direta do script
    tags = get_trending_hashtags_with_views()
    print("\nHashtags virais do dia:")
    hashtags_disponiveis = [tag_info['hashtag'].replace('#', '').lower() for tag_info in tags]
    for tag_info in tags:
        print(f"{tag_info['hashtag']} - Visualizações: {tag_info['visualizacoes']}")
    print("\nDigite as hashtags que deseja baixar os links, separadas por vírgula (ex: anime,booktokbrasil ou #anime,#booktokbrasil):")
    hashtags_input = input().strip()
    print("Quantos links válidos por hashtag você deseja baixar?")
    try:
        qtd = int(input().strip())
    except ValueError:
        qtd = 5
    run_tiktok_downloader(hashtags_input, qtd)
