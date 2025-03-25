from typing import Dict, Optional
from datetime import datetime
import asyncio
import aiohttp
import json

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
                await self.send_webhook_response(
                    request_id,
                    error="Já existe uma solicitação em processamento. Tente novamente mais tarde."
                )
                return False

            self._queue[request_id] = {
                'file_id': file_id,
                'webhook_url': webhook_url,
                'status': 'pending',
                'created_at': datetime.now().isoformat(),
                'error': None,
                'result': None
            }
            self._processing = True
            return True

    async def update_status(self, request_id: str, status: str, error: Optional[str] = None, result: Optional[str] = None):
        if request_id in self._queue:
            self._queue[request_id].update({
                'status': status,
                'error': error,
                'result': result,
                'updated_at': datetime.now().isoformat()
            })

            # Se o status for final (completed ou error), libera o processamento
            if status in ['completed', 'error']:
                async with self._lock:
                    self._processing = False

    async def send_webhook_response(self, request_id: str, login_url: Optional[str] = None, error: Optional[str] = None):
        response_data = {
            'request_id': request_id,
            'status': 'error' if error else self._queue.get(request_id, {}).get('status', 'unknown')
        }

        if error:
            response_data['error'] = error
        elif request_id in self._queue:
            request_data = self._queue[request_id]
            response_data.update({
                'created_at': request_data['created_at'],
                'updated_at': request_data.get('updated_at')
            })

            if login_url:
                response_data['login_url'] = login_url

            if request_data['error']:
                response_data['error'] = request_data['error']

            if request_data['result']:
                response_data['transcription'] = request_data['result']

        try:
            webhook_url = self._queue.get(request_id, {}).get('webhook_url')
            if webhook_url:
                async with aiohttp.ClientSession() as session:
                    await session.post(
                        webhook_url,
                        json=response_data,
                        headers={'Content-Type': 'application/json'}
                    )
        except Exception as e:
            print(f"Error sending webhook: {e}")

    def get_request_status(self, request_id: str) -> Optional[dict]:
        return self._queue.get(request_id)
