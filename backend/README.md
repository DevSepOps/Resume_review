# Resume Review - Backend

FastAPI service in Lich architecture (`app/cmd`, `app/internal`, `app/api`, `app/pkg`).

- Architecture: `docs/architecture/backend-architecture.md`
- Features: `docs/features/backend/`
- Runbook (run, test, deploy, migrate): `docs/runbooks/backend/backend-api.md`
- Troubleshooting: `docs/troubleshooting/backend.md`
- API/env contract: `docs/architecture/contracts.md`

Quick start:

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
pytest                                   # tests use SQLite, no setup needed
DATABASE_URL=... JWT_SECRET_KEY=... python -m app.cmd.server
```
