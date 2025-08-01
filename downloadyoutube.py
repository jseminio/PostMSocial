from playwright.sync_api import sync_playwright
import time
import os
import yt_dlp

def buscar_links_youtube(termos, quantidade_de_links_validos=5):
    """
    Busca links de vídeos públicos do YouTube para cada termo informado.
    Parâmetros:
        termos (list): lista de termos de busca (palavras-chave ou hashtags sem #)
        quantidade_de_links_validos (int): quantidade máxima de links válidos por termo
    Retorna:
        dict: {termo: [lista de links]}
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
            # Rola a página para carregar mais vídeos
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
    while True:
        print("\nDigite os termos (hashtags ou palavras) para buscar vídeos no YouTube, separados por vírgula (ex: futebol,tecnologia):")
        termos_input = input().strip()
        termos_escolhidos = []
        for t in termos_input.split(','):
            t_clean = t.strip().replace('#', '')
            if t_clean:
                termos_escolhidos.append(t_clean)
        if not termos_escolhidos:
            print("Nenhum termo válido selecionado. Tente novamente.")
            continue
        print("Quantos links válidos por termo você deseja baixar?")
        try:
            qtd = int(input().strip())
        except ValueError:
            print("Quantidade inválida. Tente novamente.")
            continue
        links_por_termo = buscar_links_youtube(termos_escolhidos, quantidade_de_links_validos=qtd)
        for termo, links in links_por_termo.items():
            print(f"\nLinks encontrados para '{termo}':")
            for link in links:
                print(link)
            if not links:
                print("Nenhum link encontrado ou a página demorou para carregar.")
            else:
                print(f"\nIniciando download dos vídeos para '{termo}'...")
                baixar_videos(links)
        print("\nDeseja buscar links de mais termos? (s/n)")
        resposta = input().strip().lower()
        if resposta != 's':
            print("Encerrando o programa.")
            break

if __name__ == "__main__":
    main()
