#!/bin/bash

# TinyFish Financial Agent - Deployment Script

echo "🐟 Deploying TinyFish Financial Agent"
echo ""

# Build Docker image
echo "🏗️  Building Docker image..."
docker-compose build

# Run tests in container
echo "🧪 Running tests..."
docker-compose run --rm agent pytest tests/ -v

if [ $? -ne 0 ]; then
    echo "❌ Tests failed. Aborting deployment."
    exit 1
fi

# Start all services
echo "🚀 Starting all services..."
docker-compose up -d

echo "✅ Deployment complete!"
echo ""
echo "Services running:"
docker-compose ps

echo ""
echo "View logs: docker-compose logs -f agent"
