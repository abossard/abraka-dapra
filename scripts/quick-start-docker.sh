#!/bin/bash
# Quick start script for Abraka-Dapra Docker setup

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Abraka-Dapra Docker Compose Quick Start                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check prerequisites
echo -e "${BLUE}[1/6]${NC} Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: docker is not installed${NC}"
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    echo -e "${RED}ERROR: docker compose is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Docker and Docker Compose are installed"
echo ""

# Build images
echo -e "${BLUE}[2/6]${NC} Building Docker images..."
docker compose build
echo -e "${GREEN}✓${NC} Images built successfully"
echo ""

# Start services
echo -e "${BLUE}[3/6]${NC} Starting services..."
docker compose up -d

# Wait for services
echo -e "${BLUE}[4/6]${NC} Waiting for services to be ready..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8000/healthz > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Services are ready!"
        break
    fi
    attempt=$((attempt + 1))
    printf "."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "\n${RED}ERROR: Services did not become ready in time${NC}"
    echo "Check logs with: docker compose logs"
    exit 1
fi
echo ""

# Initialize Ollama (optional)
echo -e "${BLUE}[5/6]${NC} Initialize Ollama model? (optional, takes 5-10 minutes)"
echo -e "This step pulls the LLM model into Ollama container."
read -p "Do you want to pull the model now? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Pulling model: deepseek-r1:8b..."
    if docker exec abraka-ollama ollama pull deepseek-r1:8b; then
        echo -e "${GREEN}✓${NC} Model pulled successfully"
    else
        echo -e "${YELLOW}WARNING: Failed to pull model. You can do this later with:${NC}"
        echo "  make docker-init-ollama"
    fi
else
    echo -e "${YELLOW}Skipped. Run 'make docker-init-ollama' when ready.${NC}"
fi
echo ""

# Run tests
echo -e "${BLUE}[6/6]${NC} Running end-to-end tests..."
if command -v python3 &> /dev/null; then
    if python3 -m pip list 2>/dev/null | grep -q requests; then
        python3 tests/e2e_docker_test.py
    else
        echo -e "${YELLOW}WARNING: 'requests' module not found. Installing...${NC}"
        python3 -m pip install requests --quiet
        python3 tests/e2e_docker_test.py
    fi
else
    echo -e "${YELLOW}WARNING: Python3 not found, skipping tests${NC}"
fi
echo ""

# Summary
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🎉 Abraka-Dapra is now running!                          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Service Endpoints:"
echo -e "  • Agent Shell:        ${BLUE}http://localhost:8000${NC}"
echo -e "  • Agent Shell Health: ${BLUE}http://localhost:8000/healthz${NC}"
echo -e "  • Ollama:             ${BLUE}http://localhost:11434${NC}"
echo -e "  • Zipkin UI:          ${BLUE}http://localhost:9411${NC}"
echo -e "  • Agent Dapr:         ${BLUE}http://localhost:3500/v1.0/metadata${NC}"
echo -e "  • Workflow Dapr:      ${BLUE}http://localhost:3601/v1.0/metadata${NC}"
echo ""
echo -e "Useful Commands:"
echo -e "  • View logs:          ${BLUE}make docker-logs${NC}"
echo -e "  • Stop services:      ${BLUE}make docker-down${NC}"
echo -e "  • Run tests:          ${BLUE}make docker-test${NC}"
echo -e "  • Init Ollama:        ${BLUE}make docker-init-ollama${NC}"
echo ""
echo -e "Documentation:"
echo -e "  • Docker Setup:       ${BLUE}docs/DOCKER_SETUP.md${NC}"
echo -e "  • Main README:        ${BLUE}README.md${NC}"
echo ""
