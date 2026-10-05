# Build context MUST be backend/ :
#   docker build -f deployments/docker/backend/Dockerfile -t rr-backend:dev backend
# compose: build: { context: ../../backend, dockerfile: ../deployments/docker/backend/Dockerfile }
#   (dockerfile path is resolved relative to the context)

# ---- builder: resolve dependencies into a venv ----
FROM python:3.12-slim-bookworm AS builder
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /build
COPY requirements.txt .
RUN pip install -r requirements.txt

# ---- runtime ----
FROM python:3.12-slim-bookworm AS runtime
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UPLOAD_DIR=/app/data/uploads

RUN groupadd --gid 10001 app \
 && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin app \
 && mkdir -p /app/data/uploads \
 && chown -R 10001:10001 /app

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY --chown=10001:10001 app/ app/
COPY --chown=10001:10001 migrations/ migrations/
COPY --chown=10001:10001 alembic.ini .
COPY --chown=10001:10001 entrypoint.sh /entrypoint.sh
RUN chmod 0555 /entrypoint.sh

USER 10001:10001
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).status == 200 else 1)"]

ENTRYPOINT ["/entrypoint.sh"]
