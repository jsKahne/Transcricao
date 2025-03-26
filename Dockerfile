# Estágio de construção
FROM python:3.11-slim as builder

# Instalar dependências do sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Configurar diretório de trabalho
WORKDIR /app

# Clonar o repositório
RUN git clone https://github.com/jsKahne/Transcricao.git /tmp/src && \
    cp -r /tmp/src/* /app/ && \
    rm -rf /tmp/src

# Instalar dependências Python
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Imagem final
FROM python:3.11-slim

# Instalar ffmpeg e curl
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Configurar diretório de trabalho
WORKDIR /app

# Copiar arquivos do estágio de construção
COPY --from=builder /app /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Comando para iniciar a aplicação
CMD ["python", "main.py"]
