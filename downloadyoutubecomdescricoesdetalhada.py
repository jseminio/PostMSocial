from playwright.sync_api import sync_playwright
import time
import os
import yt_dlp
from datetime import datetime, timedelta

def buscar_links_youtube(termos, quantidade_de_links_validos=5):
    """
    Busca links de vídeos públicos do YouTube para cada termo informado,
    filtrando apenas vídeos enviados nas últimas 24h e ordenando por visualizações.
    Retorna informações detalhadas dos vídeos.
    """
    resultado = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for termo in termos:
            print(f"\nBuscando vídeos para: {termo}")
            # url = f"https://www.youtube.com/results?search_query={termo}&sp=EgQIBRAB"  # Filtro: Hoje + Ordenar por: Visualizações
            url = f"https://www.youtube.com/results?search_query={termo}&sp=CAISBAgFEAE%253D"  # Filtro: Este Ano + Ordenar por: Visualizações
            print(f"URL: {url}")
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
            browser.close()

            # Filtrar vídeos enviados nas últimas 24h e ordenar por visualizações
            infos_videos = []
            for link in video_links:
                try:
                    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                        info = ydl.extract_info(link, download=False)
                    # upload_date pode não estar presente, então usar upload_timestamp se possível
                    upload_timestamp = info.get('upload_timestamp')
                    if upload_timestamp:
                        upload_time = datetime.fromtimestamp(upload_timestamp)
                    elif info.get('upload_date'):
                        upload_time = datetime.strptime(info['upload_date'], "%Y%m%d")
                    else:
                        continue
                    now = datetime.now()
                    if (now - upload_time) <= timedelta(hours=24):
                        view_count = info.get('view_count', 0)
                        infos_videos.append({
                            'link': link,
                            'view_count': view_count,
                            'upload_time': upload_time,
                            'title': info.get('title', ''),
                            'duration': info.get('duration', 0),
                            'description': info.get('description', ''),
                            'comment_count': info.get('comment_count', 0)
                        })
                except Exception:
                    continue
            # Ordena por visualizações (decrescente)
            infos_videos.sort(key=lambda x: x['view_count'], reverse=True)
            resultado[termo] = infos_videos[:quantidade_de_links_validos]
    return resultado

def formatar_tempo(segundos):
    minutos, s = divmod(segundos, 60)
    horas, m = divmod(minutos, 60)
    if horas:
        return f"{horas}h {m}m {s}s"
    elif m:
        return f"{m}m {s}s"
    else:
        return f"{s}s"

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
    for video in links:
        link = video['link']
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
        for termo, videos in links_por_termo.items():
            print(f"\nVídeos encontrados para '{termo}':")
            if not videos:
                print("Nenhum vídeo encontrado ou a página demorou para carregar ou não há vídeos das últimas 24h.")
            else:
                for idx, video in enumerate(videos, 1):
                    print(f"\n[{idx}] Título: {video['title']}")
                    print(f"    Link: {video['link']}")
                    print(f"    Data de envio: {video['upload_time'].strftime('%d/%m/%Y %H:%M')}")
                    print(f"    Duração: {formatar_tempo(video['duration'])}")
                    print(f"    Visualizações: {video['view_count']}")
                    print(f"    Comentários: {video['comment_count']}")
                    desc = video['description'] or ""
                    print(f"    Descrição: {desc[:200]}{'...' if len(desc) > 200 else ''}")
                print(f"\nIniciando download dos vídeos para '{termo}'...")
                baixar_videos(videos)
        print("\nDeseja buscar links de mais termos? (s/n)")
        resposta = input().strip().lower()
        if resposta != 's':
            print("Encerrando o programa.")
            break

if __name__ == "__main__":
    main()
