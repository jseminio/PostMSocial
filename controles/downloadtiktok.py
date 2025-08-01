from playwright.sync_api import sync_playwright
import time
import os
import yt_dlp

def get_trending_hashtags_with_views():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # Página de tendências TikTok (ajuste conforme país/região)
        page.goto("https://www.tiktok.com/discover")
        # Aguarda mais tempo para garantir o carregamento dos elementos
        page.wait_for_selector('a[href^="/tag/"]', timeout=15000)
        time.sleep(2)  # Espera extra para garantir carregamento
        # Busca as hashtags (links)
        hashtag_elements = page.query_selector_all('a[href^="/tag/"]')
        hashtags = []
        for elem in hashtag_elements:
            tag = elem.inner_text()
            if tag.startswith("#"):
                # Busca o elemento pai e irmãos para encontrar visualizações
                parent = elem.evaluate_handle('node => node.parentElement')
                views = None
                if parent:
                    # Procura por todos os spans ou divs irmãos
                    siblings = parent.query_selector_all('span, div')
                    for sib in siblings:
                        sib_text = sib.inner_text().strip()
                        # Procura por padrão de número + views/visualizações
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
    Parâmetros:
        hashtags (list): lista de hashtags (sem o #)
        quantidade_de_links_validos (int): quantidade máxima de links válidos por hashtag
    Retorna:
        dict: {hashtag: [lista de links]}
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
            # Rola a página para baixo várias vezes para tentar carregar mais vídeos
            for _ in range(10):
                page.mouse.wheel(0, 3000)
                time.sleep(1.5)
            # Busca todos os links de vídeo possíveis
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
    """
    download_dir = os.path.join(os.path.dirname(__file__), '../downloads')
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
    """
    Função principal que orquestra o processo de download de vídeos do TikTok.

    Este loop interativo primeiro busca e exibe as hashtags em alta. Em seguida, solicita ao usuário
    que escolha as hashtags e a quantidade de vídeos a serem baixados. Com base na entrada,
    chama as funções para obter os links dos vídeos e, finalmente, baixá-los.
    O loop continua até que o usuário decida parar.
    """
    while True:
        tags = get_trending_hashtags_with_views()
        print("\nHashtags virais do dia:")
        hashtags_disponiveis = [tag_info['hashtag'].replace('#', '').lower() for tag_info in tags]
        for tag_info in tags:
            print(f"{tag_info['hashtag']} - Visualizações: {tag_info['visualizacoes']}")
        print("\nDigite as hashtags que deseja baixar os links, separadas por vírgula (ex: anime,booktokbrasil ou #anime,#booktokbrasil):")
        hashtags_input = input().strip()
        hashtags_escolhidas = []
        for h in hashtags_input.split(','):
            h_clean = h.strip().replace('#', '').lower()
            if h_clean in hashtags_disponiveis:
                hashtags_escolhidas.append(h_clean)
        if not hashtags_escolhidas:
            print("Nenhuma hashtag válida selecionada. Tente novamente.")
            continue
        print("Quantos links válidos por hashtag você deseja baixar?")
        try:
            qtd = int(input().strip())
        except ValueError:
            print("Quantidade inválida. Tente novamente.")
            continue
        links_por_hashtag = obter_links_hashtag(hashtags_escolhidas, quantidade_de_links_validos=qtd)
        for hashtag, links in links_por_hashtag.items():
            print(f"\nLinks autorizados para download em #{hashtag}:")
            for link in links:
                print(link)
            if not links:
                print("Nenhum link autorizado encontrado ou a página demorou para carregar.")
            else:
                print(f"\nIniciando download dos vídeos da hashtag #{hashtag}...")
                baixar_videos(links)
        print("\nDeseja buscar links de mais hashtags? (s/n)")
        resposta = input().strip().lower()
        if resposta != 's':
            print("Encerrando o programa.")
            break

if __name__ == "__main__":
    main()
