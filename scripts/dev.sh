#!/bin/bash

# TinyFish Financial Agent - Development Script

echo "🐟 Starting TinyFish Financial Agent Development Environment"
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "Please edit .env with your API keys before continuing."
    exit 1
fi

# Start Docker services
echo "🐳 Starting Docker services (Redis + Postgres)..."
docker-compose up -d redis postgres

echo "⏳ Waiting for services to be ready..."
sleep 5

# Run tests
echo "🧪 Running tests..."
pytest tests/ -v

if [ $? -eq 0 ]; then
    echo "✅ Tests passed!"
else
    echo "❌ Tests failed. Please fix before continuing."
    exit 1
fi

# Start the agent
echo "🚀 Starting agent..."
python -m src.agent.core

echo ""
echo "Development environment ready!"
