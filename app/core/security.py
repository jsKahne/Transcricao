from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
import secrets

# Gerar uma API key segura
API_KEY = "cascade_" + secrets.token_urlsafe(32)
API_KEY_NAME = "X-API-Key"

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if not api_key_header or api_key_header != API_KEY:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, 
            detail="Invalid API Key"
        )
    return api_key_header
