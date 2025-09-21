# Dapr Components

This directory holds the resource definitions used by Operation Snacktopus. The active `statestore.yaml` points at Redis, so make sure a Redis instance is available on `localhost:6379` before running the multi-app template.

To enable additional integrations, remove the `.disabled` suffix and provide the backing service:

- `ollama.yaml.disabled` – OpenAI-compatible connector aimed at a local Ollama instance; requires `OPENAI_API_KEY` or the file secret store.
- `pubsub.yaml.disabled` – Redis pub/sub configuration for workflow fan-out telemetry.
- `secretstore.yaml.disabled` – File-based secret store that feeds the Ollama component.

If you re-enable these manifests, ensure the corresponding infrastructure is running (Redis, Ollama) and update `manifests/dapr.yaml` environment variables as needed.
