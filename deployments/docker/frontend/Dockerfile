# syntax=docker/dockerfile:1
# Build context: frontend/   ->   docker build -f deployments/docker/frontend/Dockerfile -t rr-frontend:dev frontend
FROM python:3.12-slim-bookworm AS builder
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
COPY requirements.txt /tmp/requirements.txt
RUN /opt/venv/bin/pip install -r /tmp/requirements.txt

FROM python:3.12-slim-bookworm AS runtime
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLET_FORCE_WEB_SERVER=true \
    FLET_HOST=0.0.0.0 \
    FLET_PORT=8001 \
    UPLOAD_TMP_DIR=/tmp/uploads

RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app \
    && mkdir -p /tmp/uploads \
    && chown app:app /tmp/uploads

COPY --from=builder /opt/venv /opt/venv
WORKDIR /app
# Code stays root-owned (read-only for the app user); only the download staging dir is writable.
COPY src/ /app/
RUN mkdir -p /app/assets/downloads && chown app:app /app/assets/downloads && chmod 0700 /app/assets/downloads

USER 10001:10001
EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8001/', timeout=4).status == 200 else 1)"]

CMD ["python", "main.py"]
