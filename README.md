# ResumeReview
<p align="center">
  <img src="./assets/Logo.png" alt="Logo" width="230" height="230">
</p>
<p align="center">
  <img src="./assets/API.png" alt="Logo" width="220" height="220">
  <img src="./assets/login.png" alt="Logo" width="220" height="220">
  <img src="./assets/register.png" alt="Logo" width="220" height="220">
  <img src="./assets/resume.png" alt="Logo" width="220" height="220">
</p>
A modern full-stack project to upload, manage, and review CVs/resumes, showcasing DevOps, backend, frontend, infrastructure, and observability best practices.

**Technologies:**
<p align="center">
  <img src="https://github.com/tandpfun/skill-icons/blob/main/icons/FastAPI.svg" height="40" />
  <img src="https://flet.dev/img/logo.svg" height="40" />
  <img src="https://github.com/tandpfun/skill-icons/blob/main/icons/Python-Light.svg" height="40" />
  <img src="https://github.com/tandpfun/skill-icons/blob/main/icons/Terraform-Light.svg" height="40" />
  <img src="https://github.com/tandpfun/skill-icons/blob/main/icons/Ansible.svg" height="40" />
  <img src="https://github.com/tandpfun/skill-icons/blob/main/icons/Elasticsearch-Light.svg" height="40" />
  <img src="https://github.com/tandpfun/skill-icons/blob/main/icons/Grafana-Light.svg" height="40" />
  <img src="https://cdn.worldvectorlogo.com/logos/traefik-1.svg" height="40" />
  <img src="https://github.com/tandpfun/skill-icons/blob/main/icons/Docker.svg" height="40" />
  <img src="https://github.com/tandpfun/skill-icons/blob/main/icons/PostgreSQL-Light.svg" height="40" />
  <img src="https://github.com/pytest-dev/design/blob/master/pytest_logo/pytest_logo.svg" height="40" />
  <img src="https://github.com/tandpfun/skill-icons/blob/main/icons/GithubActions-Light.svg" height="40" />
  <img src="https://github.com/tandpfun/skill-icons/blob/main/icons/AWS-Light.svg" height="40" />
  <img src="https://github.com/tandpfun/skill-icons/blob/main/icons/Azure-Light.svg" height="40" />
</p>
```

## 📂 Repository Structure (brief)

```
.
├── .github
│   └── workflows
│       └── ci.yml
├── backend
│   ├── app
│   ├── requirements.txt
│   └── (other backend modules)
├── frontend
│   └── (Flet UI application)
├── IaC
│   └── (Terraform and Ansible modules / configs)
├── monitoring
│   └── (ELK+Grafana / metrics scaffolding)
├── traefik
│   └── dynamic configuration, middleware rules
├── docker-compose.prod.yml
├── LICENSE
└── README.md
```
### ⚙️ Frontend and backend structure

<pre>
                      ┌─────────────────┐    HTTP Requests    ┌─────────────────┐
                      │    Frontend     │ ←────────────────→  │    Backend      │
                      │   (Flet UI)     │    JSON Responses   │   (FastAPI)     │
                      └─────────────────┘                     └─────────────────┘
                              │                                      │
                              └───────────── API Client ─────────────┘
</pre>
## ✨ Features & Capabilities

- Backend API with **FastAPI** for authentication, resume upload, metadata management  
- Frontend UI built in **Flet** (Python-based)  
- SandBox: Vagrant as IaC and Virtualbox as virtualization for testing
- Docker / Docker Compose setup for local development  
- CI/CD pipeline: tests, builds, and Docker image pushes  
- Infrastructure-as-Code (IaC) examples with Terraform modules for both AWS and Azure
- Configure management: Ansible playbooks
- Reverse-proxy and routing via **Traefik**  
- Observability & logging stack (Elasticsearch + metricbeats + Logstash + Grafana)  

---

## 🚀 Quick Start (Local Development)

### Prerequisites

- Docker & Docker Compose  
- Python 3.12+  
- Git  

### Setup & Run

```bash
git clone https://github.com/DevSepOps/Resume_review.git
cd Resume_review

# Copy your environment file and configure it
cp backend/app/.env.example backend/app/.env
# Edit .env with your DB url, JWT secret, etc.

# Make sure to edit docker-compose.prod.yml and enter your domain and subdomains
vim docker-compose.prod.yml

docker compose -f docker-compose.prod.yml --env-file ./backend/app/.env up -d --build 
```

Services that should start:

- **backend** (FastAPI)  
- **frontend** (Flet UI)  
- **postgres** database  
- **traefik** (reverse-proxy) 
- **Portainer** (Docker containers and images management)  
- **ELK Stack + Grafana** (Monitoring Stack)  

You can access:

- Backend API: `http://api.yourdomain` (OpenAPI docs under `/docs`)  
- Frontend: `http://yourdomain`
- Traefik `http://traefik.yourdomain/dashboard/`  
- Grafana `http://grafana.yourdomain/`  

---

## 🛠 Environment Variables

In `backend/app/.env`, configure:

```
SQLALCHEMY_DATABASE_URL=postgresql://{user}:{password}@postgres:5432/{db_name}
POSTGRES_USER="user"
POSTGRES_PASSWORD="pass"
POSTGRES_DB="db_name"
JWT_SECRET_KEY=your_jwt_secret
SECRET_KEY=some_secret_key
DEBUG=True
ENVIRONMENT="development"
AUTO_MIGRATE="true"  # Set to "false" in production if you want manual control
# Add other variables if required
```

---

## 🧱 Database Migrations

If you're using Alembic:

```bash
cd backend
alembic init alembic
# Configure alembic.ini / env.py with SQLALCHEMY_DATABASE_URL
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

---

## ✅ Testing

```bash
cd backend
pytest -v --junitxml=report.xml --cov=app --cov-report=xml
```

The CI workflow runs these tests automatically.

---

## 📦 CI / CD Pipeline

- On push or pull request to `main` / `dev` or workflow_dispatch(manually): run tests job  
- On success in `main`: build and push Docker image  
- Optionally, deploy (e.g. via Terraform / Kubernetes) using subsequent steps | 🔧 Under development​ ⚠️​  

See `.github/workflows/backend-ci-cd.yml` and `.github/workflows/frontend-ci-cd.yml` for the pipeline definition.

---

## 📊 Monitoring & Logging

- **Logs**: structured JSON logs from backend → ELK pipeline (Filebeat → Logstash → Elasticsearch → Grafana/Kibana)  
- **Metrics**: instrumentation (response times, error rates) → Grafana dashboards  
- Future plans: alerting, more advanced metrics, dashboards  

---

## ⚠️ Troubleshooting & Common Issues

| Problem | Possible Fix |
|---|---|
| Traefik fails to get TLS certificate | Ensure DNS A record points to server, bypass CDN for `/.well-known` or use DNS challenge |
| ImportError in CI for missing functions | Add missing `decode_refresh_token` or adjust test imports |
| DB not reachable in CI | Match service name `postgres` in `SQLALCHEMY_DATABASE_URL` (e.g. `postgres:5432`) |

---

## 🤝 Contributing & Guidelines

- Fork the project  
- Create a feature branch  
- Write tests for your changes  
- Submit a PR  
- Follow style (black, flake8)  
- Document new features / config changes  

---

## 📄 License & Contact

- License: MIT  
- Maintainer: Sepehr Maadani - sepehrmaadani98@gmail.com  
- Feel free to use or adapt this for your own portfolios or refer to this as a sample DevOps setup  

