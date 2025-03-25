# Video Transcription API

API para transcrição de vídeos do Google Drive usando Whisper.

## Características

- Autenticação via API Key
- Integração com Google Drive
- Transcrição usando OpenAI Whisper
- Sistema de fila (uma transcrição por vez)
- Notificações via webhook
- Suporte a múltiplos idiomas

## Requisitos

- Python 3.11+
- FFmpeg
- Docker (opcional)

## Configuração

1. Clone o repositório:
```bash
git clone <seu-repositorio>
cd <seu-diretorio>
```

2. Configure as credenciais do Google Drive:
- Coloque seu arquivo `credentials.json` na raiz do projeto
- Na primeira execução, você será solicitado a autenticar com o Google Drive

3. Configure a variável de ambiente com sua API Key:
```bash
export API_KEY="sua_api_key"
```

## Instalação

### Usando Docker (Recomendado)

1. Construa e inicie os containers:
```bash
docker-compose up -d
```

### Instalação Manual

1. Crie um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Instale o FFmpeg:
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows (usando Chocolatey)
choco install ffmpeg
```

4. Inicie o servidor:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Uso

### Autenticação

Todas as requisições devem incluir o header `X-API-Key` com sua chave de API.

### Endpoints

#### POST /api/v1/transcribe

Inicia uma transcrição de vídeo.

**Request:**
```json
{
    "file_id": "id_do_video_no_drive",
    "webhook_url": "url_para_receber_resultado",
    "language": "pt"  // opcional
}
```

**Response:**
```json
{
    "status": "queued",
    "message": "Solicitação adicionada à fila",
    "request_id": "id_unico_da_requisicao"
}
```

### Respostas do Webhook

#### Sucesso:
```json
{
    "request_id": "id_da_requisicao",
    "status": "completed",
    "transcription": "texto_transcrito"
}
```

#### Erro:
```json
{
    "request_id": "id_da_requisicao",
    "status": "error",
    "error": "mensagem_do_erro"
}
```

#### Necessidade de Autenticação:
```json
{
    "request_id": "id_da_requisicao",
    "status": "auth_required",
    "error": "Autenticação necessária",
    "login_url": "url_para_autorizacao_google"
}
```

## Códigos de Erro

- `401`: API Key inválida
- `429`: Já existe uma solicitação em processamento
- `500`: Erro interno do servidor

## Notas

- Apenas uma transcrição é processada por vez
- O token do Google Drive é permanente após a primeira autenticação
- Os arquivos temporários são limpos automaticamente após o processamento
