# Multi-stage build for abraka-dapra services
FROM python:3.13-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src ./src

# Install uv package manager
# Try the official installer first, fall back to pip if it fails
RUN curl -LsSf https://astral.sh/uv/install.sh | sh || pip install --no-cache-dir uv
ENV PATH="/root/.cargo/bin:${PATH}"

# Install dependencies
RUN uv sync --frozen

# Agent shell service
FROM base AS agent-shell
ENV SERVICE_NAME=agent-shell
ENV AGENT_HTTP_PORT=8000
ENV AGENT_SIDECAR_PORT=3500
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "src.agent_shell.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Workflow host service
FROM base AS workflow-host
ENV SERVICE_NAME=workflow-host
ENV WORKFLOW_SIDECAR_PORT=3601
CMD ["uv", "run", "python", "src/workflow_host/main.py"]
