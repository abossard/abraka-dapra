#!/bin/bash
# Script to initialize Ollama with required model in Docker environment

set -e

echo "Waiting for Ollama service to be ready..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:11434/ > /dev/null 2>&1; then
        echo "Ollama is ready!"
        break
    fi
    attempt=$((attempt + 1))
    echo "Attempt $attempt/$max_attempts - Ollama not ready yet, waiting..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "ERROR: Ollama did not become ready in time"
    exit 1
fi

echo ""
echo "Pulling model: deepseek-r1:8b"
echo "This may take a while depending on your internet connection..."
docker exec abraka-ollama ollama pull deepseek-r1:8b

echo ""
echo "Model successfully pulled!"
echo "You can now use the model in your applications."
