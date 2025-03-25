import whisper
from moviepy.editor import VideoFileClip
import logging
from pathlib import Path
from app.core.config import settings
import os
import time

logger = logging.getLogger(__name__)

# Adicionar FFmpeg ao PATH
os.environ["PATH"] = os.environ["PATH"] + os.pathsep + r"C:\ProgramData\chocolatey\lib\ffmpeg\tools\ffmpeg\bin"

class TranscriptionService:
    def __init__(self):
        self.model = None

    def _load_model(self):
        """Carrega o modelo Whisper se ainda não estiver carregado"""
        if self.model is None:
            logger.info(f"Carregando modelo Whisper: {settings.WHISPER_MODEL}")
            self.model = whisper.load_model(settings.WHISPER_MODEL)

    def extract_audio(self, video_path: Path, audio_path: Path) -> None:
        """Extrai áudio do vídeo"""
        try:
            video_path_str = str(video_path.absolute())
            audio_path_str = str(audio_path.absolute())
            
            logger.info(f"Extraindo áudio de {video_path_str}")
            video = VideoFileClip(video_path_str)
            
            if video.audio is None:
                raise ValueError("O vídeo não contém áudio")
            
            video.audio.write_audiofile(audio_path_str)
            video.close()
            
            # Aguardar um momento para garantir que o arquivo foi escrito
            time.sleep(1)
            
            if not os.path.exists(audio_path_str):
                raise FileNotFoundError(f"Arquivo de áudio não foi criado: {audio_path_str}")
                
            logger.info(f"Áudio extraído com sucesso: {audio_path_str}")
            
        except Exception as e:
            logger.error(f"Erro ao extrair áudio: {e}")
            raise
        finally:
            try:
                video.close()
            except:
                pass

    def transcribe(self, audio_path: Path, language: str = None) -> str:
        """Transcreve o áudio para texto"""
        try:
            self._load_model()
            
            audio_path_str = str(audio_path.absolute())
            logger.info(f"Verificando arquivo de áudio: {audio_path_str}")
            
            if not os.path.exists(audio_path_str):
                raise FileNotFoundError(f"Arquivo de áudio não encontrado: {audio_path_str}")
            
            # Verificar tamanho do arquivo
            file_size = os.path.getsize(audio_path_str)
            logger.info(f"Tamanho do arquivo de áudio: {file_size} bytes")
            
            if file_size == 0:
                raise ValueError(f"Arquivo de áudio está vazio: {audio_path_str}")

            # Verificar permissões
            if not os.access(audio_path_str, os.R_OK):
                raise PermissionError(f"Sem permissão para ler o arquivo: {audio_path_str}")

            logger.info(f"Iniciando transcrição do arquivo: {audio_path_str}")
            
            # Configurar opções de transcrição
            options = {}
            if language:
                options["language"] = language
            
            result = self.model.transcribe(audio_path_str, **options)
            
            logger.info("Transcrição concluída com sucesso")
            return result["text"]
            
        except Exception as e:
            logger.error(f"Erro na transcrição: {e}")
            raise
