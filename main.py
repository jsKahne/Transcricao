from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import os
import logging
import aiohttp
import asyncio
import whisper
from moviepy.editor import VideoFileClip
import shutil
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import router
from app.models.schemas import TranscriptionRequest, ConversionRequest

# Configuração de logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # URL do frontend React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Escopo necessário para acessar o Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Diretório para arquivos temporários
TEMP_DIR = "temp_files"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

class ConversionRequest(BaseModel):
    file_id: str
    webhook: str

def get_drive_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token_file:
            token_file.write(creds.to_json())
    
    return build('drive', 'v3', credentials=creds)

async def download_file(service, file_id):
    try:
        file_metadata = service.files().get(fileId=file_id).execute()
        logging.info(f"Metadados do arquivo: {file_metadata}")

        request_drive = service.files().get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request_drive)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            logging.info(f"Progresso do download: {int(status.progress() * 100)}%")

        return file.getvalue(), file_metadata['name']
    except Exception as e:
        logging.error(f"Erro ao baixar arquivo: {e}")
        raise

def convert_video_to_audio(video_path, audio_path):
    try:
        video = VideoFileClip(video_path)
        if video.audio is None:
            raise ValueError("O vídeo não contém áudio")
        
        video.audio.write_audiofile(audio_path)
        video.close()
        logging.info(f"Áudio extraído com sucesso: {audio_path}")
    except Exception as e:
        logging.error(f"Erro na conversão do vídeo para áudio: {e}")
        raise

def transcribe_audio(audio_path):
    try:
        logging.info("Carregando modelo Whisper...")
        model = whisper.load_model("base")
        
        logging.info(f"Iniciando transcrição do arquivo: {audio_path}")
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Arquivo de áudio não encontrado: {audio_path}")
            
        result = model.transcribe(audio_path)
        logging.info("Transcrição concluída com sucesso")
        
        return result["text"]
    except Exception as e:
        logging.error(f"Erro na transcrição: {e}")
        raise

async def send_webhook(webhook_url, text):
    try:
        async with aiohttp.ClientSession() as session:
            webhook_data = {"text": text}
            async with session.post(webhook_url, json=webhook_data) as response:
                if response.status != 200:
                    raise HTTPException(status_code=500, detail="Falha ao enviar webhook")
        logging.info("Webhook enviado com sucesso")
    except Exception as e:
        logging.error(f"Erro ao enviar webhook: {e}")
        raise

# Manter a rota antiga para compatibilidade
@app.post("/convert")
async def convert_legacy(request: ConversionRequest, background_tasks: BackgroundTasks):
    """Rota legada para manter compatibilidade"""
    from app.api.routes import process_transcription
    
    # Converter request antigo para novo formato
    new_request = TranscriptionRequest(
        file_id=request.file_id,
        webhook_url=request.webhook
    )
    
    # Processar usando a nova função
    if new_request.webhook_url:
        # Processamento assíncrono com webhook
        background_tasks.add_task(
            process_transcription,
            new_request.file_id,
            str(new_request.webhook_url)
        )
        return {
            "status": "processing",
            "message": "Transcrição iniciada. O resultado será enviado para o webhook."
        }
    else:
        # Processamento síncrono
        transcription = await process_transcription(new_request.file_id)
        return {
            "status": "completed",
            "message": "Transcrição concluída com sucesso",
            "transcription": transcription
        }

# Incluir novas rotas
app.include_router(router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
