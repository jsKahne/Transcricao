from typing import Dict, Optional
from datetime import datetime
import asyncio
import aiohttp
import json
import logging

logger = logging.getLogger(__name__)

class QueueManager:
    _instance = None
    _queue: Dict[str, dict] = {}
    _processing = False
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(QueueManager, cls).__new__(cls)
        return cls._instance

    async def add_to_queue(self, request_id: str, file_id: str, webhook_url: str) -> bool:
        """Adiciona uma solicitação à fila. Retorna False se já houver uma solicitação em processamento."""
        async with self._lock:
            if self._processing:
                logger.info(f"Requisição {request_id} rejeitada: já existe processamento em andamento")
                await self.send_webhook_response(
                    request_id,
                    error="Já existe uma solicitação em processamento. Tente novamente mais tarde."
                )
                return False

            logger.info(f"Adicionando requisição {request_id} à fila")
            self._queue[request_id] = {
                'file_id': file_id,
                'webhook_url': webhook_url,
                'status': 'pending',
                'stage': 'queued',
                'created_at': datetime.now().isoformat(),
                'error': None,
                'result': None
            }
            self._processing = True
            return True

    async def update_status(self, request_id: str, status: str, stage: str, progress: Optional[dict] = None, error: Optional[str] = None, result: Optional[str] = None):
        """
        Atualiza o status de uma requisição.
        progress é usado apenas para logs no console, não é enviado no webhook
        """
        if request_id in self._queue:
            # Atualizar dados básicos
            self._queue[request_id].update({
                'status': status,
                'stage': stage,
                'updated_at': datetime.now().isoformat()
            })
            
            # Registrar progresso no log (não vai para o webhook)
            if progress:
                logger.info(f"Requisição {request_id}: {stage} - {progress['percentage']}% - {progress['details']}")
            
            if error:
                self._queue[request_id]['error'] = error
                logger.error(f"Erro na requisição {request_id}: {error}")
                # Enviar webhook imediatamente em caso de erro
                await self.send_webhook_response(request_id)
            
            if result:
                self._queue[request_id]['result'] = result
                logger.info(f"Requisição {request_id} concluída com sucesso")
                # Enviar webhook com o resultado
                await self.send_webhook_response(request_id)

            # Se o status for final (completed ou error), libera o processamento
            if status in ['completed', 'error']:
                async with self._lock:
                    self._processing = False
                    logger.info(f"Processamento da requisição {request_id} finalizado. Fila liberada.")

    async def send_webhook_response(self, request_id: str, login_url: Optional[str] = None, error: Optional[str] = None):
        """Envia apenas erros, URL de login ou resultado final para o webhook"""
        if request_id not in self._queue:
            return

        request_data = self._queue[request_id]
        response_data = {
            'request_id': request_id
        }

        # Adiciona URL de login se necessário
        if login_url:
            response_data['login_url'] = login_url
            response_data['error'] = "Autenticação necessária"

        # Adiciona erro se houver
        elif error or request_data.get('error'):
            response_data['error'] = error or request_data['error']

        # Adiciona resultado se disponível
        elif request_data.get('result'):
            response_data['transcription'] = request_data['result']

        # Se não houver login_url, erro ou resultado, não envia webhook
        if not (login_url or error or request_data.get('error') or request_data.get('result')):
            return

        try:
            webhook_url = request_data.get('webhook_url')
            if webhook_url:
                logger.info(f"Enviando resposta webhook para requisição {request_id}")
                async with aiohttp.ClientSession() as session:
                    await session.post(
                        webhook_url,
                        json=response_data,
                        headers={'Content-Type': 'application/json'}
                    )
        except Exception as e:
            logger.error(f"Erro ao enviar webhook para requisição {request_id}: {e}")

    def get_request_status(self, request_id: str) -> Optional[dict]:
        return self._queue.get(request_id)
