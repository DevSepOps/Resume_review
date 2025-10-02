#!/bin/bash

echo "🚀 Setting up Resume Review API..."
echo

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from example..."
    cp env.example .env
    echo "❌ Please edit .env file and set your values before running docker-compose"
    echo "   Important: Change POSTGRES_PASSWORD, JWT_SECRET_KEY, SECRET_KEY"
    exit 1
else
    echo "✅ .env file already exists"
fi

echo "🐳 Starting Docker containers..."
docker-compose up -d --build

echo "🎯 Setup complete! API is running on http://localhost:8000"