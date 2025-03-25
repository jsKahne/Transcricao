from pydantic import BaseModel, HttpUrl
from typing import Optional

class ConversionRequest(BaseModel):
    """Modelo para requisições no formato antigo"""
    file_id: str
    webhook: Optional[HttpUrl] = None

class TranscriptionRequest(BaseModel):
    """Modelo para requisições no novo formato"""
    file_id: str
    webhook_url: HttpUrl
    language: Optional[str] = None
    save_to_drive: bool = False

class TranscriptionResponse(BaseModel):
    """Modelo para respostas de transcrição"""
    status: str
    message: str
    request_id: Optional[str] = None
    transcription: Optional[str] = None
    file_url: Optional[str] = None

class ErrorResponse(BaseModel):
    """Modelo para respostas de erro"""
    detail: str
