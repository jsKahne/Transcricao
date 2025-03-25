FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copiar arquivos do projeto
COPY requirements.txt .
COPY app/ ./app/
COPY main.py .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Expor porta
EXPOSE 8000

# Comando para iniciar a aplicação
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
