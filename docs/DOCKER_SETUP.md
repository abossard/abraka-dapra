# Docker Compose Setup for Abraka-Dapra

This document describes how to run the entire Abraka-Dapra stack using Docker Compose, including Dapr, Ollama, Redis, and all services.

## Overview

The Docker Compose setup includes:

- **Redis**: State store and pub/sub backend
- **Ollama**: Local LLM service for AI agents
- **Zipkin**: Distributed tracing (optional)
- **Dapr Placement**: Actor placement service
- **Agent Shell**: FastAPI service with Dapr sidecar
- **Workflow Host**: Dapr Workflow runtime with Dapr sidecar

## Prerequisites

- Docker Engine 20.10+ and Docker Compose V2
- At least 4GB of available RAM (8GB recommended for Ollama)
- ~10GB of disk space for Ollama models

## Quick Start

### 1. Build the Docker images

```bash
make docker-build
```

Or manually:

```bash
docker compose build
```

### 2. Start all services

```bash
make docker-up
```

Or manually:

```bash
docker compose up -d
```

### 3. Initialize Ollama with a model

This step pulls the LLM model into the Ollama container. It may take 5-10 minutes depending on your internet connection.

```bash
make docker-init-ollama
```

Or manually:

```bash
./scripts/init-ollama.sh
```

### 4. Run end-to-end tests

```bash
make docker-test
```

Or manually:

```bash
python3 tests/e2e_docker_test.py
```

### 5. View logs

```bash
make docker-logs
```

Or manually:

```bash
docker compose logs -f
```

### 6. Stop all services

```bash
make docker-down
```

Or manually:

```bash
docker compose down
```

## Service Endpoints

When running with Docker Compose, the following endpoints are available on your host machine:

- **Agent Shell**: http://localhost:8000
  - Health check: http://localhost:8000/healthz
  - Root endpoint: http://localhost:8000/
- **Agent Shell Dapr Sidecar**: http://localhost:3500
  - Metadata: http://localhost:3500/v1.0/metadata
- **Workflow Host Dapr Sidecar**: http://localhost:3601
  - Metadata: http://localhost:3601/v1.0/metadata
- **Redis**: localhost:6379
- **Ollama**: http://localhost:11434
- **Zipkin UI**: http://localhost:9411

## Architecture

The Docker Compose setup uses a sidecar pattern for Dapr:

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Network                          │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Redis      │  │   Ollama     │  │   Zipkin     │    │
│  │   :6379      │  │   :11434     │  │   :9411      │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                             │
│  ┌──────────────┐                                          │
│  │  Placement   │                                          │
│  │   :50006     │                                          │
│  └──────────────┘                                          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Agent Shell Container                              │  │
│  │  ┌────────────┐         ┌────────────┐            │  │
│  │  │ agent-shell│◄────────┤agent-shell │            │  │
│  │  │    app     │         │    dapr    │            │  │
│  │  │   :8000    │         │   :3500    │            │  │
│  │  └────────────┘         └────────────┘            │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Workflow Host Container                            │  │
│  │  ┌────────────┐         ┌────────────┐            │  │
│  │  │ workflow-  │◄────────┤workflow-   │            │  │
│  │  │   host     │         │  host-dapr │            │  │
│  │  │            │         │   :3601    │            │  │
│  │  └────────────┘         └────────────┘            │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

Each Dapr sidecar shares the network namespace with its application container using `network_mode: "service:<app>"`, allowing them to communicate over localhost.

## Components

Dapr components are configured differently for Docker networking:

- **Local development** (components/*.yaml): Uses `localhost` for Redis and Ollama
- **Docker** (components/docker/*.yaml): Uses Docker service names (`redis`, `ollama`)

The Docker Compose setup automatically mounts the `components/docker/` directory for Dapr sidecars.

## Troubleshooting

### Services won't start

Check if the ports are already in use:

```bash
netstat -tuln | grep -E '(6379|8000|11434|9411|3500|3601|50006)'
```

### Ollama is slow or not responding

Ollama requires significant resources. Ensure you have:
- At least 4GB of free RAM (8GB recommended)
- Model is pulled: `docker exec abraka-ollama ollama list`

Pull the model manually if needed:

```bash
docker exec abraka-ollama ollama pull deepseek-r1:8b
```

### Agent shell or workflow host can't connect to Redis

Check if Redis is running:

```bash
docker compose ps redis
docker compose logs redis
```

### Dapr sidecars not registering components

Check Dapr sidecar logs:

```bash
docker compose logs agent-shell-dapr
docker compose logs workflow-host-dapr
```

Verify components are mounted correctly:

```bash
docker compose exec agent-shell-dapr ls -la /components
```

### Reset everything

To completely reset the environment:

```bash
docker compose down -v  # Remove containers and volumes
docker compose build --no-cache  # Rebuild images
docker compose up -d  # Start fresh
```

## Development Workflow

### Making changes to Python code

The images copy source code during build. After making changes:

1. Rebuild the images: `make docker-build`
2. Restart services: `make docker-down && make docker-up`

For faster iteration during development, consider using the local Dapr setup (`make run-agent`, `make run-workflow`) instead of Docker.

### Viewing service logs

Follow all logs:
```bash
make docker-logs
```

Follow specific service logs:
```bash
docker compose logs -f agent-shell
docker compose logs -f workflow-host
docker compose logs -f agent-shell-dapr
```

### Inspecting containers

Get a shell in the agent-shell container:
```bash
docker compose exec agent-shell /bin/bash
```

Get a shell in the workflow-host container:
```bash
docker compose exec workflow-host /bin/bash
```

### Testing Ollama directly

```bash
curl -X POST http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-r1:8b",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Accessing Dapr APIs

Check agent-shell metadata:
```bash
curl http://localhost:3500/v1.0/metadata | jq
```

Check workflow-host metadata:
```bash
curl http://localhost:3601/v1.0/metadata | jq
```

Invoke a workflow:
```bash
curl -X POST http://localhost:3601/v1.0-beta1/workflows/dapr/hello_snacktopus/start?instanceID=test-$(date +%s) \
  -H "Content-Type: application/json" \
  -d '{"name": "Docker Test"}'
```

## CI/CD Integration

The end-to-end test script (`tests/e2e_docker_test.py`) can be used in CI pipelines:

```bash
# In your CI script
make docker-build
make docker-up
sleep 30  # Wait for services to be ready
make docker-test
EXIT_CODE=$?
make docker-down
exit $EXIT_CODE
```

## Resource Requirements

Minimum recommended system resources:

- **CPU**: 2 cores
- **RAM**: 4GB (8GB with Ollama model loaded)
- **Disk**: 10GB free space

For production workloads, scale up based on load.

## Additional Resources

- [Dapr Documentation](https://docs.dapr.io/)
- [Ollama Documentation](https://ollama.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Main README](../README.md)
