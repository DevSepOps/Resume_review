# Resume Review API

A secure FastAPI application for resume management and review.

## 🚀 Quick Start

### Prerequisites
- Docker
- Docker Compose

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/resume-review-api.git
   cd resume-review-api

2. **Set up environment variables Script**
    ```bash
    # On Linux/Mac
    chmod +x setup.sh
    ./setup.sh

    # On Windows
    .\setup.ps1

3. **Edit the .env file with your secure values**

    ```bash
    POSTGRES_USER="your_secure_username"
    POSTGRES_PASSWORD="your_very_strong_password"
    JWT_SECRET_KEY='generate_using_python -c "import secrets; print(secrets.token_urlsafe(32))"'
    SECRET_KEY='generate_using_python -c "import secrets; print(secrets.token_hex(32))"'

4. **Start the application**
    ```bash
    docker-compose up -d

5. **Access the API**

API: http://localhost:8000

Docs: http://localhost:8000/docs

### 🔧 Manual Setup
If you prefer manual setup:

1. Copy environment template:

    ```bash
    cp env.example .env

2. Edit .env with your values

3. Build and run:

    ```bash
    docker-compose up -d --build

### 🛡️ Security Notes
🔒 Never commit .env to version control

🔑 Generate new secrets for each deployment

🐳 Use Docker secrets in production


### Frontend and backend structure

The Frontend and Backend structure:
```text
┌─────────────────┐    HTTP Requests    ┌─────────────────┐
│   Frontend      │ ←────────────────→  │   Backend       │
│   (Flet UI)     │    JSON Responses   │   (FastAPI)     │
└─────────────────┘                     └─────────────────┘
         │                                      │
         └───────────── API Client ─────────────┘


🤝 Contributing
Please read our contributing guidelines before submitting pull requests.
