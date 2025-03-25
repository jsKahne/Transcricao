from pydantic_settings import BaseSettings
from pathlib import Path
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Video Transcription API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Diretórios
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    TEMP_DIR: Path = BASE_DIR / "temp_files"
    
    # Google Drive settings
    GOOGLE_SCOPES: list = ["https://www.googleapis.com/auth/drive.readonly"]
    CREDENTIALS_FILE: Path = Path("credentials.json")
    TOKEN_FILE: Path = Path("token.json")

    # Whisper settings
    WHISPER_MODEL: str = "base"

    # API Key
    API_KEY: str = os.getenv("API_KEY", "cascade_YOUR_API_KEY_HERE")  # Será substituída pela key gerada

    class Config:
        case_sensitive = True

settings = Settings()

# Criar diretório temporário se não existir
os.makedirs(str(settings.TEMP_DIR), exist_ok=True)
