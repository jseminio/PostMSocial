# processador_video.py

import argparse
import os
import json
import re
import logging
import subprocess
import tempfile
from datetime import timedelta

# Instale as dependências com:
# pip install yt-dlp openai-whisper moviepy google-generativeai python-dotenv
# Para a versão otimizada, instale também: pip install faster-whisper
import google.generativeai as genai
from dotenv import load_dotenv
from faster_whisper import WhisperModel
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.VideoClip import ColorClip
from moviepy.video.io.VideoFileClip import VideoFileClip

from moviepy.video.fx.Crop import Crop

from yt_dlp import YoutubeDL

# --- Configuração de Logging ---
# Um bom logging ajuda a entender o que está acontecendo e a depurar problemas.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- Carregamento de Configurações ---
# Carrega variáveis de ambiente (ex: API keys) de um arquivo .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("A chave da API do Gemini não foi encontrada. Defina GEMINI_API_KEY no seu arquivo .env")

genai.configure(api_key=GEMINI_API_KEY)


def download_video(url: str, output_dir: str = "downloads") -> str | None:
    """
    Baixa um vídeo de uma URL usando yt-dlp.
    Retorna o caminho do arquivo de vídeo baixado.
    """
    logging.info(f"Iniciando o download do vídeo da URL: {url}")
    os.makedirs(output_dir, exist_ok=True)
    
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': False,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            logging.info(f"Vídeo baixado com sucesso: {filename}")
            return filename
    except Exception as e:
        logging.error(f"Falha ao baixar o vídeo: {e}")
        return None


def transcribe_audio(video_path: str) -> list:
    """
    Transcreve o áudio de um arquivo de vídeo usando faster-whisper, uma implementação otimizada.
    Retorna uma lista de segmentos com texto e timestamps.
    """
    logging.info(f"Iniciando a transcrição do vídeo com faster-whisper: {video_path}")
    try:
        # --- Configuração do Modelo faster-whisper ---
        # 'base' é rápido. Para maior precisão, use 'medium' ou 'large-v3'.
        # Para usar GPU (muito mais rápido): device="cuda", compute_type="float16"
        # (Requer NVIDIA GPU, CUDA Toolkit e cuDNN)
        # Para usar CPU: device="cpu", compute_type="int8" (otimizado para CPU)
        model_size = "base"
        device = "cpu"
        compute_type = "int8"

        logging.info(f"Carregando modelo whisper '{model_size}' no dispositivo '{device}' com tipo de computação '{compute_type}'...")
        model = WhisperModel(model_size, device=device, compute_type=compute_type)

        segments_generator, info = model.transcribe(video_path, word_timestamps=True)

        # O resto do código espera uma lista de dicionários, então convertemos a saída.
        logging.info("Convertendo segmentos da transcrição...")
        result_segments = []
        for segment in segments_generator:
            segment_dict = {
                'start': segment.start,
                'end': segment.end,
                'text': segment.text,
                'words': []
            }
            for word in segment.words:
                segment_dict['words'].append({
                    'word': word.word,
                    'start': word.start,
                    'end': word.end,
                })
            result_segments.append(segment_dict)

        logging.info(f"Transcrição concluída. Idioma detectado: {info.language} com probabilidade {info.language_probability:.2f}")
        return result_segments
    except Exception as e:
        logging.error(f"Falha na transcrição com faster-whisper: {e}")
        return []


def analyze_with_gemini(transcription_text: str) -> list:
    """
    Usa a API do Gemini para encontrar clipes interessantes na transcrição.
    """
    logging.info("Analisando a transcrição com o Gemini para encontrar clipes...")
    
    # Um prompt bem definido é a chave para um bom resultado.
    # Pedir a saída em JSON facilita o processamento.
    prompt = f"""
    Analise a seguinte transcrição de um vídeo e identifique de 3 a 5 segmentos curtos e interessantes
    que seriam bons para postar como clipes em redes sociais.

    Para cada segmento, forneça:
    1.  Um título curto e chamativo em português.
    2.  O tempo de início (start_time) e o tempo de fim (end_time) em segundos.
    3.  Uma breve justificativa do porquê o clipe é interessante.

    Retorne sua resposta como uma lista de objetos JSON válidos, dentro de um bloco de código JSON.
    Exemplo de formato de saída:
    ```json
    [
      {{
        "title": "Título do Clipe 1",
        "start_time": 123.45,
        "end_time": 145.67,
        "reason": "Este clipe é interessante porque..."
      }},
      {{
        "title": "Título do Clipe 2",
        "start_time": 501.00,
        "end_time": 525.50,
        "reason": "Este clipe contém uma revelação importante."
      }}
    ]
    ```

    Transcrição:
    ---
    {transcription_text}
    ---
    """

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        # Extrai o bloco de código JSON da resposta do Gemini de forma mais robusta
        match = re.search(r"```json\s*([\s\S]+?)\s*```", response.text)
        if not match:
            logging.error("Bloco JSON não encontrado na resposta do Gemini.")
            logging.error(f"Resposta recebida: {response.text}")
            return []

        json_text = match.group(1)
        clips = json.loads(json_text)
        
        logging.info(f"Análise do Gemini concluída. {len(clips)} clipes encontrados.")
        return clips
    except (json.JSONDecodeError, Exception) as e:
        logging.error(f"Falha ao analisar a resposta do Gemini: {e}")
        logging.error(f"Resposta recebida: {response.text}")
        return []


def format_time_srt(seconds: float) -> str:
    """Converte segundos para o formato de tempo do SRT (HH:MM:SS,ms)."""
    delta = timedelta(seconds=seconds)
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = delta.microseconds // 1000
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


def create_subtitle_file(segments: list, clip_start: float, clip_end: float, srt_path: str):
    """
    Cria um arquivo .srt para um clipe específico a partir da transcrição completa.
    """
    logging.info(f"Criando arquivo de legenda para o clipe de {clip_start}s a {clip_end}s.")
    with open(srt_path, "w", encoding="utf-8") as f:
        subtitle_index = 1
        for segment in segments:
            for word in segment.get('words', []):
                word_start = word.get('start')
                word_end = word.get('end')
                
                # Verifica se a palavra está dentro do intervalo do clipe
                if word_start is not None and word_end is not None and clip_start <= word_start < clip_end:
                    # Ajusta o timestamp para o início do clipe
                    start_time_in_clip = word_start - clip_start
                    end_time_in_clip = word_end - clip_start
                    
                    f.write(f"{subtitle_index}\n")
                    f.write(f"{format_time_srt(start_time_in_clip)} --> {format_time_srt(end_time_in_clip)}\n")
                    f.write(f"{word.get('word', '').strip()}\n\n")
                    subtitle_index += 1
    logging.info(f"Arquivo de legenda salvo em: {srt_path}")


def cut_and_subtitle_video(
    original_video_path: str,
    clips_data: list,
    transcription_segments: list,
    output_dir: str = "clips"
):
    """
    Corta o vídeo original e adiciona legendas embutidas usando FFmpeg.
    """
    logging.info("Iniciando o processo de corte e legendagem dos clipes.")
    os.makedirs(output_dir, exist_ok=True)

    with VideoFileClip(original_video_path) as video:
        for i, clip_info in enumerate(clips_data):
            start_time = clip_info['start_time']
            end_time = clip_info['end_time']
            title = clip_info['title'].replace(" ", "_").replace("/", "-")
            
            output_filename_temp = os.path.join(output_dir, f"temp_clip_{i+1}.mp4")
            final_output_filename = os.path.join(output_dir, f"clip_{i+1}_{title}.mp4")
            
            logging.info(f"Processando clipe {i+1}/{len(clips_data)}: '{clip_info['title']}'")

            # 1. Cortar o vídeo com moviepy e formatar para 9:16
            logging.info(f"Cortando vídeo de {start_time}s a {end_time}s.")
            subclip = video.subclipped(start_time, end_time)

            logging.info("Convertendo para formato vertical 9:16 (TikTok) com corte.")
            target_w, target_h = 1080, 1920
            target_aspect = target_w / target_h

            clip_w, clip_h = subclip.size
            clip_aspect = clip_w / clip_h

            if clip_aspect > target_aspect:
                # Vídeo mais largo que o alvo (ex: 16:9), cortar as laterais
                clip_resized = subclip.resized(height=target_h)
                crop_x = int((clip_resized.w - target_w) / 2)

                # Criar a instância Crop
                crop_effect = Crop(x1=crop_x, width=target_w)
                # Aplicar o crop ao clipe
                final_subclip = crop_effect.apply(clip_resized)

            else:
                # Vídeo mais alto que o alvo (ou igual), cortar topo/base
                clip_resized = subclip.resized(width=target_w)
                crop_y = int((clip_resized.h - target_h) / 2)

                # Criar a instância Crop
                crop_effect = Crop(y1=crop_y, height=target_h)
                # Aplicar o crop ao clipe
                final_subclip = crop_effect.apply(clip_resized)

            # Salva o clipe vertical temporário.
            # Otimizações:
            # - preset='ultrafast': acelera a codificação drasticamente. A qualidade é menor,
            #   mas é um arquivo temporário.
            # - threads=4: usa mais núcleos do processador.
            # - logger='bar': mostra uma barra de progresso para não parecer travado.
            final_subclip.write_videofile(output_filename_temp, codec="libx264", audio_codec="aac", 
                                          preset='ultrafast', threads=4, logger='bar')

            # 2. Gerar o arquivo SRT para o clipe cortado
            # Usamos um arquivo temporário para a legenda
            with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.srt', encoding='utf-8') as srt_file:
                srt_filepath = srt_file.name
            
            create_subtitle_file(transcription_segments, start_time, end_time, srt_filepath)

            # 3. Embutir legendas com FFmpeg usando um estilo mais chamativo
            # O filtro 'subtitles' do FFmpeg precisa de um caminho de arquivo com escape para o Windows.
            ffmpeg_srt_path = srt_filepath.replace('\\', '/').replace(':', '\\:')
            
            # Estilo de legenda para TikTok: fonte grande, centralizada, com fundo.
            # Você pode instalar fontes como 'Montserrat Bold' e usar aqui: FontName='Montserrat Bold'
            subtitle_style = "FontName=Arial Black,FontSize=20,PrimaryColour=&HFFFFFF,BackColour=&H99000000,BorderStyle=3,Outline=1,OutlineColour=&H00000000,Shadow=0,MarginV=100,Alignment=2"

            ffmpeg_command = [
                'ffmpeg',
                '-i', output_filename_temp,
                '-vf', f"subtitles='{ffmpeg_srt_path}':force_style='{subtitle_style}'",
                '-c:a', 'copy',
                '-y', # Sobrescrever arquivo de saída se existir
                final_output_filename
            ]
            
            logging.info("Executando FFmpeg para embutir legendas...")
            logging.info(f"Comando: {' '.join(ffmpeg_command)}")

            try:
                subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True)
                logging.info(f"Clipe final salvo em: {final_output_filename}")
            except subprocess.CalledProcessError as e:
                logging.error(f"Erro no FFmpeg ao processar {final_output_filename}:")
                logging.error(f"STDOUT: {e.stdout}")
                logging.error(f"STDERR: {e.stderr}")
            finally:
                # Limpar arquivos temporários
                if os.path.exists(output_filename_temp):
                    os.remove(output_filename_temp)
                if os.path.exists(srt_filepath):
                    os.remove(srt_filepath)


def process_video_from_url(video_url: str):
    """
    Função principal que orquestra todo o processo.
    """

    # 2. Transcrição
    transcription_segments = transcribe_audio(video_url)
    if not transcription_segments:
        return
        
    # Junta a transcrição em um único texto para o Gemini
    full_transcription_text = " ".join([seg['text'] for seg in transcription_segments])

    # 3. Análise com Gemini
    interesting_clips = analyze_with_gemini(full_transcription_text)
    if not interesting_clips:
        return

    # 4. Corte e legendagem
    cut_and_subtitle_video(video_url, interesting_clips, transcription_segments)

    logging.info("Processo concluído com sucesso!")
