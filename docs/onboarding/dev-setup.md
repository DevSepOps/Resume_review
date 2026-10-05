# Developer Setup

## Prerequisites

- Python 3.12, Docker Engine 25+ with Compose v2
- Optional: Helm 3.14+ (chart work), Terraform 1.6+ and ansible-core (infra work)

## Backend

```bash
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
pytest                                   # SQLite + temp dirs, no services needed
```

To run it against a local Postgres:

```bash
export DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/resume_review
export JWT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
alembic upgrade head
python -m app.cmd.server                 # http://localhost:8000/docs (disabled when ENVIRONMENT=production)
python -m app.cmd.create_admin --username admin --email admin@example.com
```

## Frontend

```bash
cd frontend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
pytest
FLET_SECRET_KEY=dev BACKEND_URL=http://localhost:8000 FLET_OPEN_BROWSER=true python src/main.py
```

## Full stack (closest to production)

```bash
cd deployments/docker
cp .env.example .env                       # replace every CHANGE_ME (openssl rand -hex 32)
cp proxy/secrets/htpasswd.example proxy/secrets/htpasswd   # then: htpasswd -nbB admin '<password>'
docker compose up -d --build
docker compose exec backend python -m app.cmd.create_admin --username admin --email admin@example.com
```

The proxy enforces strict SNI and gets certificates from Let's Encrypt, so it needs real DNS names.
For local work, either:

- copy `docker-compose.override.example.yml` to `docker-compose.override.yml`, which publishes
  the backend on `127.0.0.1:8000` and the frontend on `127.0.0.1:8001`, bypassing the proxy; or
- add a self-signed certificate for your local names to `proxy/dynamic.yml` under `tls.certificates`
  (see [troubleshooting/infra.md](../troubleshooting/infra.md)).

## Where things are

See [system-overview.md](../architecture/system-overview.md) and [contracts.md](../architecture/contracts.md).
