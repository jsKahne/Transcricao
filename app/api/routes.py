from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from app.models.schemas import TranscriptionRequest, TranscriptionResponse
from app.services.google_drive import GoogleDriveService
from app.services.transcription import TranscriptionService
from app.services.queue_manager import QueueManager
from app.utils.file_manager import FileManager
from app.core.security import get_api_key
import logging
import aiohttp
from pathlib import Path
import uuid
from google.auth.exceptions import RefreshError

logger = logging.getLogger(__name__)
router = APIRouter()
queue_manager = QueueManager()

@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_video(
    request: TranscriptionRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(get_api_key)
):
    """
    Endpoint para transcrever um vídeo do Google Drive
    """
    request_id = str(uuid.uuid4())
    
    try:
        # Adicionar à fila
        if not await queue_manager.add_to_queue(
            request_id=request_id,
            file_id=request.file_id,
            webhook_url=str(request.webhook_url)
        ):
            # Se retornar False, já existe uma solicitação em processamento
            raise HTTPException(
                status_code=429,
                detail="Já existe uma solicitação em processamento. Tente novamente mais tarde."
            )

        # Iniciar processamento em background
        background_tasks.add_task(
            process_transcription,
            request_id,
            request.file_id,
            str(request.webhook_url),
            request.language
        )

        return TranscriptionResponse(
            status="queued",
            message="Solicitação adicionada à fila",
            request_id=request_id
        )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na requisição de transcrição: {e}")
        await queue_manager.update_status(
            request_id=request_id,
            status="error",
            error=str(e)
        )
        if request.webhook_url:
            await queue_manager.send_webhook_response(request_id)
        raise HTTPException(status_code=500, detail=str(e))

async def process_transcription(
    request_id: str,
    file_id: str,
    webhook_url: str,
    language: str = None
) -> str:
    """Processa a transcrição em background"""
    drive_service = GoogleDriveService()
    transcription_service = TranscriptionService()
    temp_dir = None
    
    try:
        # Atualizar status
        await queue_manager.update_status(request_id, "processing")
        
        # Criar diretório temporário
        temp_dir = FileManager.create_temp_directory()
        
        try:
            # Download do vídeo
            video_content, video_name = await drive_service.download_file(file_id)
        except RefreshError:
            # Se houver erro de autenticação, enviar URL de login
            login_url = drive_service.get_authorization_url()
            await queue_manager.update_status(
                request_id=request_id,
                status="auth_required",
                error="Autenticação necessária"
            )
            await queue_manager.send_webhook_response(request_id, login_url=login_url)
            return
        
        video_path = temp_dir / "video.mp4"
        audio_path = temp_dir / "audio.mp3"
        
        # Salvar vídeo
        FileManager.save_bytes_to_file(video_content, video_path)
        
        # Verificar se o vídeo foi salvo corretamente
        if not FileManager.ensure_file_exists(video_path):
            raise FileNotFoundError(f"Erro ao salvar arquivo de vídeo: {video_path}")
        
        # Extrair áudio
        transcription_service.extract_audio(video_path, audio_path)
        
        # Verificar se o áudio foi extraído corretamente
        if not FileManager.ensure_file_exists(audio_path):
            raise FileNotFoundError(f"Erro ao extrair áudio: {audio_path}")
        
        # Transcrever
        transcription = transcription_service.transcribe(audio_path, language)
        
        # Atualizar status e enviar resultado
        await queue_manager.update_status(
            request_id=request_id,
            status="completed",
            result=transcription
        )
        await queue_manager.send_webhook_response(request_id)
                
        return transcription
        
    except Exception as e:
        logger.error(f"Erro no processamento da transcrição: {e}")
        await queue_manager.update_status(
            request_id=request_id,
            status="error",
            error=str(e)
        )
        await queue_manager.send_webhook_response(request_id)
        raise
    finally:
        # Limpar arquivos temporários
        if temp_dir:
            FileManager.cleanup_directory(temp_dir)
