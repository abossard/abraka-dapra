Operation Snacktopus Specification
=================================

Mission Intent
--------------
- Deliver durable snack-recommendation experience powered by Dapr Agents + Dapr Workflows.
- Keep human approval in the loop before serving playful or risky menu items.
- Maintain clear boundaries between agent responsibilities, deterministic workflow orchestration, and external integrations.

Solution Topology
-----------------
- Two primary services: `agent-shell` (multi-agent facade) and `workflow-host` (orchestrator).
- Shared Dapr components: conversation (Ollama), state store (Redis), pubsub (Redis), secret store (local file or env), configuration (optional defaults).
- Human approval captured via workflow external event and logged to telemetry pubsub.

APIs (HTTP unless noted)
------------------------
- `POST /ask` (agent-shell): request snack suggestions; body `{question, session_id?}`; returns `{answer, sessionId, metrics, flags}`.
- `POST /history` (agent-shell): provide recent transcript summaries; body `{session}`; returns `{summaries, embeddingsRef}`.
- `POST /profile` (agent-shell): fetch user taste profile; body `{session}`; returns `{preferences}`.
- `POST /safety` (agent-shell): risk screen prompt; body `{question}`; returns `{riskLevel, rationale}`.
- `POST /human/decision` (agent-shell or optional moderator UI): pushes approval outcome into workflow via Dapr Workflow `raiseEvent`.
- Workflow management (workflow-host sidecar via Dapr REST): start `snacktopus` instance, query status, raise `humanApproval`, terminate, purge.
- Pubsub topic `workflow-metrics`: emits `{instanceId, stage, duration, verdict, humanNotes?}` for monitoring.

Workflow Outline (snacktopus)
-----------------------------
- Start: ingest payload `{question, session}`.
- Activity fan-out: invoke `/history`, `/profile`, `/safety` in parallel.
- Aggregation: enrich question with context snapshots.
- Agent call: invoke `/ask` with enriched payload; collect draft answer + confidence + human flag.
- Decision gate: if draft requires human validation, wait on external event `humanApproval` (timeout, rejection path).
- Finalization: log metrics via pubsub, persist summary to state, emit completion event.

Agent Collective Intent
-----------------------
- Durable User Agent: orchestrates agent-side workflows, manages session memory, coordinates evaluations.
- History Agent: retrieves and summarizes previous snack exchanges.
- Profile Agent: exposes stored preferences, allergies, and humor tolerance.
- Embedding Agent: produces similarity vectors for recall triggers (optional stub).
- Safety Agent: flags questionable ingredients or tone issues pre-answer.
- Answer Agent: crafts playful snack response with citations.
- Evaluator Agent: scores pun quality, safety alignment, and decides if human approval needed.
- Memory Agent (Summarizer + Pruner): curates rolling state to keep durable context lean.

State & Files Required
----------------------
- `components/` folder containing: `statestore.yaml`, `ollama.yaml`, `pubsub.yaml`, optional `secrets.yaml`.
- `prompts/` directory for agent prompt templates (history, answer, evaluator, safety).
- `workflows/` definitions: high-level YAML or Markdown describing `snacktopus` steps plus Python/JS scaffolding later.
- `manifests/` for Dapr app definitions (app-id, ports, scopes).
- Docs: `README.md`, `LOCAL_AGENT_WORKFLOW.md`, this spec.
- `configs/` for environment defaults (e.g., `.env`, deploy manifests).

Dapr Components
---------------
- `conversation.openai` named `ollama`: points to `http://localhost:11434/v1`, `model=deepseek-r1:8b`, `key=ollama` (arbitrary non-empty), `scopes: [agent-shell, workflow-host]`.
- `state.redis` named `statestore`: `redisHost=localhost:6379`, `actorStateStore=true`, `redisDB=0`.
- `pubsub.redis` named `events`: `redisHost=localhost:6379`, `consumerID=workflow-host` (optional), used for metrics + notifications.
- `secretstores.local.file` (optional) named `localsecret`: `secretsFile=./secrets.json` for API keys; otherwise env vars.
- `configuration.file` (optional) for thresholds (human approval flag, safety weights).

Operational Behavior
--------------------
- All agent calls travel through Dapr sidecar invocation to ensure consistent telemetry and retries.
- Workflow uses deterministic retries for state access; any non-deterministic reasoning stays inside agent call boundary.
- Human approval path includes timeout fallback → mark request as `rejected_timeout` and publish event.
- Metric events and agent logs must capture `sessionId`, `instanceId`, risk levels, and human notes for audit.
- Memory summarization occurs after each finalized answer; pruner removes stale entries to keep Redis lean.
- Zipkin tracer enabled for debugging; events aggregated under namespace `snacktopus`.
