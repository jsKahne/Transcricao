import whisper
import subprocess
from pathlib import Path
import logging
from typing import Optional, Callable

logger = logging.getLogger(__name__)

class TranscriptionService:
    def __init__(self):
        self.model = whisper.load_model("base")
        logger.info("Modelo Whisper carregado com sucesso")

    def extract_audio(self, video_path: Path, output_path: Path):
        """Extrai áudio de um vídeo usando FFmpeg"""
        logger.info(f"Iniciando extração de áudio do vídeo: {video_path}")
        try:
            command = [
                'ffmpeg', '-i', str(video_path),
                '-vn',  # Desabilita vídeo
                '-acodec', 'libmp3lame',  # Usa codec MP3
                '-ar', '44100',  # Sample rate
                '-ac', '2',  # Canais de áudio
                '-b:a', '192k',  # Bitrate
                str(output_path),
                '-y'  # Sobrescreve arquivo se existir
            ]
            
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Erro ao extrair áudio: {stderr.decode()}")
                raise Exception(f"Erro ao extrair áudio: {stderr.decode()}")
                
            logger.info(f"Áudio extraído com sucesso: {output_path}")
            
        except Exception as e:
            logger.error(f"Erro ao executar FFmpeg: {str(e)}")
            raise

    def transcribe(self, audio_path: Path, language: Optional[str] = None, progress_callback: Optional[Callable[[int, int], None]] = None) -> str:
        """
        Transcreve um arquivo de áudio usando Whisper
        
        Args:
            audio_path: Caminho para o arquivo de áudio
            language: Código do idioma (opcional)
            progress_callback: Função de callback para progresso (opcional)
            
        Returns:
            str: Texto transcrito
        """
        try:
            logger.info(f"Iniciando transcrição do áudio: {audio_path}")
            
            # Configurar opções do Whisper
            options = {
                "language": language if language else None,
                "task": "transcribe",
                "verbose": True
            }

            # Função de callback personalizada para o Whisper
            def whisper_callback(current: int, total: int):
                if progress_callback:
                    progress_callback(current, total)
                logger.info(f"Progresso da transcrição: {int((current/total)*100)}%")

            # Realizar transcrição
            result = self.model.transcribe(
                str(audio_path),
                **options,
                progress_callback=whisper_callback
            )
            
            logger.info("Transcrição concluída com sucesso")
            return result["text"]
            
        except Exception as e:
            logger.error(f"Erro durante a transcrição: {str(e)}")
            raise
