Write-Host "🚀 Setting up Resume Review API..." -ForegroundColor Green

# Check if .env exists
if (-not (Test-Path .env)) {
    Write-Host "📝 Creating .env file from example..." -ForegroundColor Yellow
    Copy-Item env.example .env
    Write-Host "❌ Please edit .env file and set your values before running docker-compose" -ForegroundColor Red
    Write-Host "   Important: Change POSTGRES_PASSWORD, JWT_SECRET_KEY, SECRET_KEY" -ForegroundColor Red
    exit 1
} else {
    Write-Host "✅ .env file already exists" -ForegroundColor Green
}

Write-Host "🐳 Starting Docker containers..." -ForegroundColor Yellow
docker-compose up -d --build

Write-Host "🎯 Setup complete! API is running on http://localhost:8000" -ForegroundColor Green