from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import os
import logging
from app.core.config import settings
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

class GoogleDriveService:
    def __init__(self):
        self.service = self._get_service()
        self._flow = None

    def _get_service(self):
        """Configura e retorna o serviço do Google Drive"""
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except:
                    creds = None
            
            if not creds:
                self._flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = self._flow.run_local_server(port=0)
                
            # Salvar as credenciais para a próxima execução
            with open('token.json', 'w') as token_file:
                token_file.write(creds.to_json())
        
        logger.info("Autenticado com sucesso no Google Drive")
        return build('drive', 'v3', credentials=creds)

    def get_authorization_url(self) -> str:
        """Retorna a URL para autorização do Google Drive"""
        if not self._flow:
            self._flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
        auth_url, _ = self._flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        return auth_url

    async def download_file(self, file_id: str):
        """Faz o download de um arquivo do Google Drive"""
        try:
            file_metadata = self.service.files().get(fileId=file_id).execute()
            logger.info(f"Metadados do arquivo: {file_metadata}")

            request_drive = self.service.files().get_media(fileId=file_id)
            file = io.BytesIO()
            downloader = MediaIoBaseDownload(file, request_drive)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                logger.info(f"Download progresso: {int(status.progress() * 100)}%")

            return file.getvalue(), file_metadata['name']
            
        except Exception as e:
            logger.error(f"Erro ao baixar arquivo: {e}")
            raise
