FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Uploaded-file store (ephemeral on hosts without a persistent disk).
RUN mkdir -p data/uploads

EXPOSE 8000

# Bootstrap the DB (create schema on a fresh DB, else migrate), then serve.
CMD ["sh", "-c", "python bootstrap.py && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
