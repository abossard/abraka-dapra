# Dapr Components

This directory contains the manifests that the Snacktopus services share when they run under Dapr:

- `statestore.yaml` – Redis state store (actors enabled) for session memory and saga ledger.
- `pubsub.yaml` – Redis pub/sub feed for workflow metrics and event fan-out.
- `ollama.yaml` – Conversation connector targeting the local Ollama instance via the OpenAI-compatible API.
- `secretstore.yaml` – File-based secret store used to supply the Ollama API key and other local secrets.
- `secrets.json.sample` – Example secret payload; copy to `components/secrets.json` and adjust credentials before running locally.

The manifests scope every component to the `agent-shell` and `workflow-host` apps. Update scopes if you introduce additional services.
