# Codex Implementation Guidance

Operation Snacktopus code should reflect two guiding texts:

1. **Grokking Simplicity (Eric Normand)** – Favour clear data flow, isolate mutation, and model complex behaviour with explicit event pipelines and pure transformations. Keep calculations (pure functions) separate from actions (I/O, network, Dapr sidecar calls), and make state transitions obvious through well-named reducers or workflow activities.
2. **A Philosophy of Software Design (John Ousterhout)** – Reduce complexity by creating deep modules with minimal cognitive load. Encapsulate details, define sharp interfaces, and invest in comments when the underlying ideas would otherwise leak out. Strive for consistent terminology and avoid accumulation of "glue" code without purpose.

## Working Agreements

- **Design for comprehension first.** Prefer small, composable functions in shared modules; each should have a single clear purpose and document "why" when the decision is subtle.
- **Separate actions from calculations.** In agents and workflows, wrap side-effecting calls (Dapr clients, Redis, Ollama) in explicit service layers, keeping business logic testable through pure functions.
- **Make state transitions explicit.** Durable memory updates, saga ledgers, and approval flows should use domain-specific data structures instead of ad-hoc dicts; model intent with typed objects.
- **Hide incidental complexity.** Group I/O wiring, retries, and telemetry plumbing behind helper modules so route handlers and workflow definitions read at a storytelling level.
- **Communicate trade-offs.** When shortcuts are unavoidable, capture the rationale in code comments or ADR-style notes so future contributors can revisit with context.

Place new code paths through this lens before landing changes. If an implementation feels complex, revisit these principles and consider refactoring toward clearer boundaries or better terminology.
