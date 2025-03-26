FROM python:3.11-slim

# Evita problemas de cache e reduz tamanho
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Etapa 1: build dos wheels (cache opcional para acelerar)
FROM python:3.11-slim as builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
        ffmpeg \
        curl \
        && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN mkdir /app/wheels && \
    pip wheel --wheel-dir=/app/wheels -r requirements.txt

# Etapa 2: imagem final
FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        curl \
        && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia os arquivos e roda a instalação com fallback no PyPI
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

RUN pip install --no-cache-dir --find-links=/wheels -r requirements.txt && \
    rm -rf /wheels

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]