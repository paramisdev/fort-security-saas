# syntax=docker/dockerfile:1

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# uv — быстрый установщик зависимостей.
RUN pip install --no-cache-dir uv

RUN useradd --create-home --uid 1000 appuser

WORKDIR /app

COPY --chown=appuser:appuser requirements.txt ./
RUN uv pip install --system -r requirements.txt

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

# Миграции и идемпотентный сидинг выполняются перед стартом приложения.
CMD ["sh", "-c", "alembic upgrade head && python -m scripts.seed && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
