Operation Snacktopus Test & Load Strategy
========================================

Scope
-----
- Validate functional correctness across agents, workflow orchestration, human-in-loop path, telemetry, and memory durability.
- Exercise local self-hosted deployment (Redis + Ollama) and slim multi-terminal operations.
- Demonstrate load characteristics and resource ceilings for higher traffic.

Prerequisites
-------------
- Same runtime stack as spec (`dapr init --slim`, Redis, Ollama `deepseek-r1:8b`, Python env).
- Test data: sample snack prompts, user profiles, safety rule matrix.
- Observability: Zipkin open on `http://localhost:9411`, pubsub consumer logging events, structured logs captured.
- Test harness tools: `pytest`, `pytest-asyncio`, `locust` (or `k6`), `hey` for quick bursts, `redis-cli` for inspection.

End-to-End Test Matrix
----------------------
- **Happy Path**: POST `/ask` via workflow start → automatic approval (Evaluator says no human needed) → confirm final answer, memory summary, pubsub event contents.
- **Human Approval Accept**: Workflow flags human gate → use `raiseEvent` with `approved=true`; assert workflow status `RUNNING` → `COMPLETED`, metrics show approval timestamp, memory logged.
- **Human Approval Reject**: `approved=false` event → expect workflow failure or compensating logic; verify answer suppressed, audit log recorded.
- **Human Approval Timeout**: do not raise event; confirm workflow transitions to timeout handling (e.g., `FAILED` with reason `rejected_timeout`) and pubsub event emitted.
- **Safety Block**: Safety agent returns `HIGH`; ensure workflow short-circuits before human gate, answer replaced with mitigation message, risk telemetry captured.
- **Memory Recall**: Start session with name preference, ask second question after new workflow invocation with same `session`; answer should reference stored info (check Redis and response body).
- **Profile Absent**: `/profile` returns empty; ensure fallback defaults apply and no crash.
- **Parallel Fan-out Failure**: Force `/history` failure (e.g., 500); workflow should continue with degraded context and emit warning metric.
- **Pubsub Delivery**: Subscribe test consumer, ensure single message per completion with correct schema.
- **Telemetry Trace**: Trace spans present for agent invocation + workflow activities (Zipkin), confirm tags `sessionId`, `instanceId`.
- **Scaling Agents**: Run two `agent-shell` instances (different `--app-port`) and ensure deterministic session dispatch via Dapr service invocation.

Test Automation Outline
-----------------------
- `tests/conftest.py`: fixtures to start/stop Dapr processes (agent + workflow) using subprocess + readiness polling.
- `tests/test_workflow_e2e.py`: asynchronous tests hitting workflow REST API and verifying agent responses.
- `tests/test_agent_memory.py`: direct invocation of `/ask` and Redis introspection to confirm memory summarization.
- `tests/test_safety_paths.py`: simulate risky prompts and check responses, metrics, state.
- `tests/test_pubsub.py`: run lightweight subscriber (FastAPI or Python script) to assert pubsub payload structure.
- Use `pytest-asyncio` for concurrency, `tenacity` for polling workflow status.
- On teardown, flush Redis (`FLUSHALL`), stop Dapr processes, clean `.dapr/components` temp data.

Manual Verification Checklist
-----------------------------
- Observe logs in both terminals: agent prints evaluation scores, workflow logs step transitions.
- Zipkin trace shows fan-out branch and human wait state.
- `redis-cli KEYS '*snacktopus*'` returns stored summaries; ensure pruner reduces count after threshold.
- `dapr list` shows both apps running with unique app IDs, ports.

Load Test Strategy
------------------
- Tooling: `locust` for scenario-driven load (workflow start + human approval), `k6` or `hey` for raw HTTP concurrency.
- Baseline: Run agent + workflow with default concurrency 1. Use `locust` tasks to POST `snacktopus` start, wait for completion. Track latency, throughput, error rates.
- Stress parameters: vary concurrent users 1 → 20 for workflow start, 1 → 50 for direct `/ask` (bypassing workflow) to observe Ollama throughput.
- Human approval simulation: automated event raiser triggered after `wait_for_external_event` (poll workflow status, raise event after short delay).
- Metrics to capture: request latency, workflow runtime duration, CPU / RAM usage (via `docker stats` for Redis + placement + Ollama), agent process CPU.
- Failure thresholds: Document max sustainable concurrency before Ollama queueing >5s or Redis ops degrade.

Load Test Implementation
------------------------
- `loadtest/locustfile.py`: scenario with tasks `start_workflow`, `raise_approval`, `check_status` using Locust HTTP client; environment config for base URLs.
- `loadtest/scripts/human_approver.py`: simple async worker polling workflow instances requiring approval and sending deterministic accept/reject events.
- `loadtest/k6-workflow.js`: optional k6 script hitting workflow start endpoint with ramping stages.
- Pre-warm step: run warm-up load to prime Ollama model and caches before measuring.
- Post-test validation: ensure no stuck workflow instances (`dapr .../instances`), inspect Redis for key growth, review Zipkin for missing spans.

Reporting & Regression Gates
----------------------------
- CI: optional GitHub Actions job running smoke tests (`pytest -m smoke`) with mocked LLM (bypass Ollama) for determinism.
- Manual load tests documented with metrics table (requests/sec, P95 latency, error %).
- Release gate: pass happy path, human approval, safety block, memory recall automated tests; document latest load thresholds.
