Abraka-Dapra TODO (Super Condensed)
===================================

Legend: [ ] todo · [x] done · Tags: AGENT / WF / API / STATE / OBS / DOC / OPS

Boot the Playground
-------------------
- [ ] (AGENT, STATE) Pick language + scaffold service with Dapr sidecar, lint, tests, `make run`.
- [ ] (STATE) Define core models (Question, Answer, MemoryEntry, SummaryChunk) and deterministic IDs.
- [ ] (OPS) Add secrets + component templates (state store, pubsub, workflow) with sample values.

Minimal Agent + Workflow Loop
-----------------------------
- [ ] (AGENT) Implement Durable User Agent orchestrator plus stubs for History, Profile, Safety, Answer, Evaluator, Memory.
- [ ] (WF) Wire a Dapr Workflow that fans out enrichment, scores confidence, and stops on `humanApproval` before finalizing.
- [ ] (AGENT, STATE) Build in-memory session store with rolling summaries and pruning triggers.
- [ ] (API) Expose `POST /ask` that kicks off the workflow, returns answer, and streams agent metrics.

Kitchen-Sink Delight
--------------------
- [ ] (WF, AGENT) Script the "Operation Snacktopus" workflow runbook with manifests, prompts, and test data.
- [ ] (AGENT, OBS) Log structured events for every agent hop plus the human-in-the-loop decision.
- [ ] (DOC) Capture a quickstart showing manual approval + follow-up answer replay.
- [ ] (TEST) Add happy-path + safety-violation tests to prove the workflow pauses and resumes correctly.

Stretch (When Snacks Are Stable)
--------------------------------
- [ ] (AGENT) Swap mocks for real model + embeddings provider.
- [ ] (WF) Add branch for escalated review when risk is high.
- [ ] (OPS) Containerize local dev stack and publish multi-app Dapr run config.
