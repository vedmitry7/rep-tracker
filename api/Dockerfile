FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY api/requirements.txt /tmp/api-requirements.txt
RUN pip install --no-cache-dir -r /tmp/api-requirements.txt \
    && groupadd --system app \
    && useradd --system --gid app --create-home app

COPY --chown=app:app alembic.ini ./alembic.ini
COPY --chown=app:app api ./api

USER app

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && exec uvicorn api.app.main:app --host 0.0.0.0 --port 8000"]
