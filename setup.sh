#!/bin/bash
# Setup script for ModelHub unified AI service

set -e

echo "===================================="
echo "ModelHub Setup Script"
echo "===================================="
echo ""

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if docker compose is available (try both v1 and v2 syntax)
DOCKER_COMPOSE_CMD=""
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    echo "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✓ Docker and Docker Compose are installed"
echo ""

# Start services
echo "Starting ModelHub services..."
$DOCKER_COMPOSE_CMD up -d

echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check if services are running
if docker ps | grep -q "modelhub-ollama" && docker ps | grep -q "modelhub-api"; then
    echo "✓ Services are running"
else
    echo "Warning: Some services may not be running properly"
    echo "Check logs with: docker-compose logs"
fi

echo ""
echo "===================================="
echo "Downloading LLM model (deepseek-r1:8b)..."
echo "This may take several minutes..."
echo "===================================="
echo ""

# Pull the model
docker exec -it modelhub-ollama ollama pull deepseek-r1:8b

echo ""
echo "===================================="
echo "Setup Complete!"
echo "===================================="
echo ""
echo "The ModelHub API is now available at: http://localhost:8000"
echo ""
echo "Test the service:"
echo "  Health check: curl http://localhost:8000/health"
echo ""
echo "API Documentation:"
echo "  Swagger UI: http://localhost:8000/docs"
echo "  ReDoc: http://localhost:8000/redoc"
echo ""
echo "Useful commands:"
echo "  View logs: docker-compose logs -f"
echo "  Stop services: docker-compose down"
echo "  Restart services: docker-compose restart"
echo ""
