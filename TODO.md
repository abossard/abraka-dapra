Operation Snacktopus TODO (Python Focus)
=======================================

Legend: [ ] todo · [x] done · Tags: PY / AGENT / WF / API / STATE / OBS / TEST / DOC / OPS

Environment & Components
------------------------
- [ ] (PY, OPS) Standardize on Python 3.13.7 (latest stable per python.org) and manage deps with `uv`; initialize `pyproject.toml` using official Dapr Python SDKs (`dapr`, `dapr-ext-workflow`, `dapr-agents`) plus Ruff + Pytest, and add `Makefile` targets (`make dev`, `make test`, `make run-agent`, `make run-workflow`).
- [ ] (OPS) Create `components/` with Redis state store, Redis pubsub, Ollama conversation connector, optional local secret store; include scoped manifests for `agent-shell` + `workflow-host`.
- [ ] (OPS) Author `.env.example` capturing Dapr/Ollama ports, model name, approval thresholds, and compensation toggles.

Agent Service (`agent-shell`)
----------------------------
- [ ] (AGENT, PY) Build FastAPI service using the Dapr Agents SDK (`dapr-agents`) for Durable User Agent orchestration; expose `/ask`, `/history`, `/profile`, `/safety`, `/human/decision`, wiring tools, evaluator heuristics, and structured logging through the SDK abstractions.
- [ ] (STATE, AGENT) Implement session memory helpers (Pydantic models for Question, Answer, MemoryEntry) and summarizer/pruner logic persisting via the Dapr state store client from the Python SDK.
- [ ] (OBS, API) Emit per-call telemetry leveraging Dapr SDK hooks (sidecar tracing context, pubsub via Dapr client) for Zipkin spans, metrics, and safety/evaluator flags.

Workflow Host (`workflow-host`)
-------------------------------
- [ ] (WF, PY) Implement `snacktopus` workflow with explicit Dapr patterns: fan-out/fan-in enrichment branches, agent invocation via service invocation, external `humanApproval` wait using the workflow event pattern, and compensating activities for rejected or unsafe outcomes.
- [ ] (WF, STATE) Persist workflow run metadata using Dapr state store SDK APIs and publish completion/compensation events to Redis pubsub via the Dapr client.
- [ ] (WF, AGENT) Provide CLI/utility (Python) that raises approval events through the Dapr Workflow client, supporting accept/reject/timeout flows and triggering compensation when needed.

Testing & Load
--------------
- [ ] (TEST) Add `pytest` suite exercising happy path, safety block, approval accept/reject/timeout, compensation rollback, memory recall, degraded fan-out; use Dapr SDK test harnesses or clients to interact with state and workflows, and a Redis fixture for clean state.
- [ ] (TEST, OBS) Write integration test asserting pubsub payload structure and Zipkin trace tags (including compensation traces) using Dapr SDK subscriptions or HTTP endpoints plus a mock subscriber.
- [ ] (TEST, OPS) Create locust (or k6) scenario + helper script that drives workflow starts via Dapr REST API, raises approval events with the Workflow SDK client, and records latency/resource stats; include stages that force compensations to observe load impact.

Docs & Runbooks
---------------
- [ ] (DOC) Update `README.md` quickstart with Python + Dapr SDK commands, workflow start example, approval walkthrough, and how each workflow pattern is exercised.
- [ ] (DOC, OPS) Document incident checklist (Redis down, Ollama offline, approval service lag, compensation loop) and recovery steps in `/docs/operations.md`, noting relevant Dapr CLI/SDK commands.
- [ ] (DOC, TEST) Record latest load-test results + acceptance criteria in `docs/OPERATION_SNACKTOPUS_TESTPLAN.md` appendices, referencing SDK-based test tooling and pattern coverage.
