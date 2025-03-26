# Usa a imagem Python slim (mais leve)
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /opt/transcricao-whisper-v1

# Instala as dependências do sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    ffmpeg \
    curl \
    python3-pip \
    python3-dev \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# Clona o repositório
RUN git clone https://github.com/jsKahne/Transcricao.git

# Define o diretório de trabalho no repositório clonado
WORKDIR /opt/transcricao-whisper-v1/Transcricao

# Instala as dependências do Python a partir do requirements.txt
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# Cria a pasta temp e ajusta permissões
RUN mkdir -p temp && chmod 777 temp

# Define variáveis de ambiente
ENV PYTHONPATH=/opt/transcricao-whisper-v1/Transcricao
ENV TZ=America/Sao_Paulo
ENV WHISPER_MODEL=tiny
ENV PROJECT_NAME="Video Transcription API"
ENV VERSION="1.0.0"

# Expõe a porta da API
EXPOSE 8000

# Comando para rodar o FastAPI com Uvicorn
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
