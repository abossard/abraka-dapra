Operation Snacktopus TODO (Python Focus)
=======================================

Legend: [ ] todo · [x] done · Tags: PY / AGENT / WF / API / STATE / OBS / TEST / DOC / OPS

Planning & Docs
---------------
- [x] (DOC) Capture `uv` workflow, repository layout, and system diagram in `README.md` to ground implementation kickoff.
- [x] (DOC) Document Codex implementation guidance aligned with *Grokking Simplicity* and *A Philosophy of Software Design*.

Environment & Components
------------------------
- [x] (PY, OPS) Standardize on Python 3.13.7 and manage deps with `uv`; initialize `pyproject.toml` using official Dapr Python SDKs (`dapr`, `dapr-ext-workflow`, `dapr-agents`) plus Ruff + Pytest, and add `Makefile` targets (`make dev`, `make test`, `make run-agent`, `make run-workflow`).
  - [x] Generate `uv` workspace (`uv init --name abraka_dapra`) and commit baseline `pyproject.toml`/`uv.lock`.
  - [x] Bake in scripts for `uv run make <target>` usage (see README "Make Targets & Runtime Flow").
  - [ ] Investigate availability of `pytest-dapr` (not discoverable on PyPI) or identify an alternative test harness for Dapr workflows.
- [x] (OPS) Create `components/` with Redis state store, Redis pubsub, Ollama conversation connector, optional local secret store; include scoped manifests for `agent-shell` + `workflow-host` and post-serve consumers.
  - [x] Ship Redis/Dapr manifests (`components/statestore.yaml`, `components/pubsub.yaml`).
  - [x] Add Ollama connector + file secret store manifests with scoped access.
  - [ ] Document production-ready secret management strategy beyond the local file store.
- [x] (OPS) Publish multi-app run template for self-hosted dev (`manifests/dapr.yaml`).
  - [ ] Extend template with config/per-app overrides (log destinations, placement host) as features solidify.
- [x] (OPS) Author `.env.example` capturing ports, model name, saga timeouts, supply flags, and compensation toggles.

Agent Service (`agent-shell`)
----------------------------
- [ ] (AGENT, PY) Build FastAPI service using the Dapr Agents SDK for Durable User Agent orchestration; expose `/ask`, `/history`, `/profile`, `/safety`, `/human/decision`, wiring tools (safety, supply, ops), evaluator heuristics, and structured logging.
- [ ] (STATE, AGENT) Implement session memory helpers (Pydantic models for Question, Answer, MemoryEntry) and summarizer/pruner logic persisting via the Dapr state store client.
- [ ] (OBS, API) Emit per-call telemetry leveraging Dapr SDK hooks (tracing context, pubsub via Dapr client) for Zipkin spans, saga flags, and compensation signals.

Workflow Host (`workflow-host`)
-------------------------------
- [ ] (WF, PY) Implement the kitchen-sink `snacktopus` workflow: fan-out enrichment activities, `call_answer_agent` invocation, saga manager waiting on event-driven human/ops/supply approvals, pre-serve check fan-out, compensation handlers (safety/human/ops/supply), and post-serve event fan-out + timers.
- [ ] (STATE, WF) Implement saga state & compensation ledger utilities (persist saga snapshots, track mutations for rollback) using the Dapr state store SDK.
- [ ] (WF, AGENT) Provide CLI/utility that raises `sagaEvent` approvals and orchestrates post-serve tasks via the Dapr Workflow client.

Testing & Load
--------------
- [ ] (TEST) Add `pytest` suite covering happy path, safety abort, human reject, ops timeout, supply abort, saga duplicate events, pre-serve failures, and post-serve fan-out; include Redis fixture and Dapr SDK clients.
- [ ] (TEST, OBS) Integrate tests asserting pubsub payloads (`workflow-metrics`, `taste-test.request`, `follow-up.schedule`) and Zipkin spans for saga + compensation paths.
- [ ] (TEST, OPS) Create locust (or k6) scenario plus helper scripts to drive workflow starts, issue saga events, trigger pre-serve failures, and capture latency/resource stats across success and compensation flows.

Docs & Runbooks
---------------
- [x] (DOC) Update `README.md` quickstart with Python + Dapr SDK commands, saga event walkthrough, and post-serve fan-out story. (See `README.md` sections "Working with Python uv", "Make Targets & Runtime Flow", and "Workflow Narrative".)
- [ ] (DOC, OPS) Document incident checklist (Redis down, Ollama offline, human UI outage, ops veto loop, supply fail) and recovery steps in `/docs/operations.md`, referencing Dapr CLI/SDK commands.
- [ ] (DOC, TEST) Record latest load-test results + acceptance criteria in `docs/OPERATION_SNACKTOPUS_TESTPLAN.md` appendices, mapping coverage to saga branches and post-event flows.
