from playwright.sync_api import sync_playwright
import time
import os
import yt_dlp

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
        # Busca por vídeos de hoje, ordenados por visualizações (filtro: Hoje + Ordenar por: Visualizações)
        url = "https://www.youtube.com/results?search_query=&sp=EgQIBRAB"  # Filtro: Hoje + Ordenar por: Visualizações
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
        resultado = list(video_links)[:quantidade_de_links_validos]
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
    Função principal que orquestra a busca e o download dos vídeos mais vistos no YouTube.

    Solicita ao usuário a quantidade de vídeos a serem baixados, chama a função `buscar_links_youtube_24h_mais_vistos`
    para obter os links e, em seguida, utiliza a função `baixar_videos` para fazer o download.
    Exibe os links encontrados e o status do download para o usuário.
    """
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
        print("Nenhum link encontrado ou a página demorou para carregar.")
    else:
        print(f"\nIniciando download dos vídeos mais visualizados nas últimas 24h...")
        baixar_videos(links)
    print("Encerrando o programa.")

if __name__ == "__main__":
    main()
