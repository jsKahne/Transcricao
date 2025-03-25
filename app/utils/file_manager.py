from pathlib import Path
import shutil
import logging
from app.core.config import settings
import os
import uuid

logger = logging.getLogger(__name__)

class FileManager:
    @staticmethod
    def create_temp_directory() -> Path:
        """Cria um diretório temporário único"""
        unique_id = str(uuid.uuid4())
        temp_dir = settings.TEMP_DIR / unique_id
        os.makedirs(str(temp_dir), exist_ok=True)
        logger.info(f"Diretório temporário criado: {temp_dir}")
        return temp_dir

    @staticmethod
    def cleanup_directory(directory: Path):
        """Remove um diretório e todo seu conteúdo"""
        try:
            if directory.exists():
                # Aguardar um momento para garantir que os arquivos não estão em uso
                import time
                time.sleep(1)
                
                # Tentar remover cada arquivo individualmente primeiro
                for file in directory.glob("*"):
                    try:
                        if file.is_file():
                            file.unlink()
                            logger.info(f"Arquivo removido: {file}")
                    except Exception as e:
                        logger.error(f"Erro ao remover arquivo {file}: {e}")
                
                # Remover o diretório
                shutil.rmtree(str(directory))
                logger.info(f"Diretório temporário removido: {directory}")
        except Exception as e:
            logger.error(f"Erro ao limpar diretório temporário: {e}")

    @staticmethod
    def save_bytes_to_file(content: bytes, filepath: Path):
        """Salva conteúdo em bytes em um arquivo"""
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(content)
            logger.info(f"Arquivo salvo em: {filepath}")
        except Exception as e:
            logger.error(f"Erro ao salvar arquivo: {e}")
            raise

    @staticmethod
    def ensure_file_exists(filepath: Path) -> bool:
        """Verifica se um arquivo existe e é acessível"""
        try:
            return filepath.exists() and filepath.is_file() and os.access(str(filepath), os.R_OK)
        except Exception as e:
            logger.error(f"Erro ao verificar arquivo {filepath}: {e}")
            return False
