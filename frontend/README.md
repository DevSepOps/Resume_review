# Resume Review - frontend

Flet 0.28.3 web app (feature-based). See the docs:

- Architecture: [docs/architecture/frontend-architecture.md](../docs/architecture/frontend-architecture.md)
- Run / deploy: [docs/runbooks/frontend/frontend-app.md](../docs/runbooks/frontend/frontend-app.md)
- Troubleshooting: [docs/troubleshooting/frontend.md](../docs/troubleshooting/frontend.md)

Quick start:

```bash
pip install -r requirements-dev.txt
FLET_SECRET_KEY=dev BACKEND_URL=http://localhost:8000 FLET_PORT=8001 python src/main.py
pytest
```
