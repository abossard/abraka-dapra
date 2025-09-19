Local Dapr Agent + Workflow Stack (Ollama deepseek-r1:8b)
========================================================

Topology Snapshot
-----------------
- Dapr sidecars (self-hosted) share `./components` (Redis state + Ollama conversation connector).
- `ollama serve` exposes OpenAI-compatible `/v1` endpoint for `deepseek-r1:8b`.
- Python agents (dapr-agents SDK) hold durable chat state in Dapr state store and call Ollama.
- Python workflow host (dapr-ext-workflow) orchestrates fan-out + human approval + telemetry.

Prerequisites
-------------
- macOS / Linux shell with Homebrew.
- Docker Desktop running (Redis container from `dapr init`).
- Ollama ≥ 0.5.0 (`brew install ollama`).
- Python ≥ 3.11.
- Dapr CLI ≥ 1.16 (`brew install dapr/tap/dapr-cli`).

Local Runtime Bring-up
----------------------
```bash
# Verify tooling
ollama --version
dapr --version
python3 --version

# Start Dapr control plane + default Redis/Zipkin (self-hosted)
dapr init --slim   # slim still provisions placement + redis + zipkin via Docker

# Pull / start the model locally
ollama pull deepseek-r1:8b
OLLAMA_HOST=127.0.0.1 ollama serve  # keep running in its own terminal
```

Components Folder (`./components`)
----------------------------------
```bash
mkdir -p components
cat <<'YAML' > components/statestore.yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: statestore
spec:
  type: state.redis
  version: v1
  metadata:
    - name: redisHost
      value: localhost:6379
    - name: redisDB
      value: "0"
    - name: actorStateStore
      value: "true"
YAML

cat <<'YAML' > components/ollama.yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: ollama
spec:
  type: conversation.openai
  version: v1
  metadata:
    - name: key
      value: "ollama"
    - name: model
      value: deepseek-r1:8b
    - name: endpoint
      value: http://localhost:11434/v1
scopes:
  - agent-shell
  - workflow-host
YAML

cat <<'YAML' > components/pubsub.yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: events
spec:
  type: pubsub.redis
  version: v1
  metadata:
    - name: redisHost
      value: localhost:6379
YAML
```

Python Environment
------------------
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install dapr dapr-ext-workflow dapr-agents fastapi uvicorn httpx
```

Reusable Env Vars
-----------------
```bash
cat <<'EOF' > .env
OPENAI_API_KEY=ollama           # dapr-agents uses OpenAI client; value must be non-empty
DAPR_GRPC_PORT=50001            # optional fixed port for agents app
DAPR_HTTP_PORT=3500
OLLAMA_BASE_URL=http://localhost:11434/v1
EOF
```

Agent Runtime Skeleton (`src/agents/runtime.py`)
-----------------------------------------------
```python
import os
from dapr_agents.agents.agent import Agent
from dapr_agents.llm.openai import OpenAIChatClient
from dapr_agents.memory.daprstatestore import ConversationDaprStateMemory
from dapr_agents.tool.http import HttpTool

ollama = OpenAIChatClient(
    model=os.getenv("OLLAMA_MODEL", "deepseek-r1:8b"),
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
    api_key=os.getenv("OPENAI_API_KEY", "ollama"),
    temperature=0.7,
)

memory = ConversationDaprStateMemory(store_name="statestore")

safety_tool = HttpTool.from_config(
    name="snack_safety_scan",
    method="POST",
    url="http://localhost:5210/safety",  # stubbed fastapi endpoint
)

durable_user_agent = Agent(
    name="durable_user",
    llm=ollama,
    memory=memory,
    tools=[safety_tool],
    tracing_namespace="snacktopus",
)

async def run_dialog(prompt: str, session_id: str | None = None) -> dict:
    if session_id:
        durable_user_agent.memory.session_id = session_id
    response = await durable_user_agent.run(prompt)
    return {
        "answer": response.output_text,
        "sessionId": durable_user_agent.memory.session_id,
        "messages": durable_user_agent.memory.get_messages(limit=50),
    }
```

Expose Agent over HTTP (`src/agents/api.py`)
-------------------------------------------
```python
from fastapi import FastAPI
from pydantic import BaseModel
from .runtime import run_dialog

app = FastAPI()

class AskPayload(BaseModel):
    question: str
    session_id: str | None = None

@app.post("/ask")
async def ask(payload: AskPayload):
    return await run_dialog(payload.question, payload.session_id)
```

Run the Agent App
-----------------
```bash
dapr run \
  --app-id agent-shell \
  --app-port 5210 \
  --dapr-http-port 3500 \
  --dapr-grpc-port 50001 \
  --resources-path ./components \
  -- python -m uvicorn src.agents.api:app --host 0.0.0.0 --port 5210
```

Workflow Host Skeleton (`src/workflows/host.py`)
-----------------------------------------------
```python
import asyncio
from datetime import timedelta
from dapr.ext.workflow import WorkflowRuntime, workflow, activity
import httpx

@activity()
async def gather_context(ctx, payload: dict) -> dict:
    async with httpx.AsyncClient(base_url="http://localhost:5210") as client:
        history, profile = await asyncio.gather(
            client.post("/history", json=payload),
            client.post("/profile", json=payload),
        )
    return {
        "history": history.json(),
        "profile": profile.json(),
    }

@activity()
async def call_agent(ctx, payload: dict) -> dict:
    async with httpx.AsyncClient(base_url="http://localhost:3500/v1.0") as client:
        resp = await client.post(
            "/invoke/agent-shell/method/ask",
            json={"question": payload["question"], "session_id": payload.get("session")},
        )
        resp.raise_for_status()
        return resp.json()

@activity()
async def persist_metrics(ctx, payload: dict):
    async with httpx.AsyncClient(base_url="http://localhost:3500/v1.0") as client:
        await client.post("/publish/events/workflow-metrics", json=payload)

@workflow()
def snacktopus(ctx, payload: dict):
    context = yield ctx.call_activity(gather_context, payload)
    draft = yield ctx.call_activity(call_agent, {**payload, **context})

    if draft.get("needs_human"):
        approval = yield ctx.wait_for_external_event(
            "humanApproval", timeout=timedelta(minutes=5)
        )
        if not approval.get("approved"):
            raise Exception("Human rejected the snack plan")
        draft["human"] = approval

    yield ctx.call_activity(persist_metrics, draft)
    return draft

async def main():
    runtime = WorkflowRuntime()
    runtime.register_workflow(snacktopus)
    runtime.register_activity(gather_context)
    runtime.register_activity(call_agent)
    runtime.register_activity(persist_metrics)
    await runtime.start()

if __name__ == "__main__":
    asyncio.run(main())
```

Run the Workflow App
--------------------
```bash
dapr run \
  --app-id workflow-host \
  --app-port 6100 \
  --dapr-http-port 3600 \
  --resources-path ./components \
  -- python src.workflows.host
```

Kick Off a Workflow Instance
----------------------------
```bash
dapr_workflow_url=http://localhost:3600/v1.0/workflows/dapr/workflow-host
curl -X POST \
  "$dapr_workflow_url/schedules/snacktopus?instanceID=demo-001" \
  -H 'Content-Type: application/json' \
  -d '{"question":"build me the Snacktopus platter","session":"demo-user"}'

curl "$dapr_workflow_url/instances/demo-001"
```

Human-in-the-loop Approval
--------------------------
```bash
curl -X POST \
  "$dapr_workflow_url/instances/demo-001/raiseEvent/humanApproval" \
  -H 'Content-Type: application/json' \
  -d '{"approved":true,"notes":"Gelatin cleared"}'
```

Tear-down & Reset
-----------------
```bash
redis-cli -h localhost FLUSHALL
```

Diagnostics Quick Hits
----------------------
- `dapr list` – verify both apps are healthy.
- `dapr dashboard` – inspect workflow history, pubsub metrics, sidecar logs.
- `docker logs dapr_redis` – ensure Redis ready.
- `curl http://localhost:11434/api/tags` – confirm `deepseek-r1:8b` is loaded.

Key Integration Notes
---------------------
- `conversation.openai` component binds Ollama because Ollama mimics OpenAI `/v1` REST; `key` metadata can be any non-empty string.
- Keep `ollama serve` bound to loopback (`OLLAMA_HOST=127.0.0.1`) to avoid LAN exposure.
- Dapr agents persist conversation chunks via gRPC to the sidecar; Redis compaction policies keep memory bounded.
- Workflow `wait_for_external_event` ensures deterministic pause for the human decision and resumes instantly when event arrives.
- Run everything under `dapr run` so workflow + agent share placement/actor metadata (`actorStateStore=true`).
- For smoke tests, post directly to `http://localhost:3500/v1.0/invoke/agent-shell/method/ask` before wiring the workflow.

Next Build Steps
----------------
- Implement FastAPI routes for `/history`, `/profile`, `/safety` so `gather_context` hits real stubs.
- Attach tracing (`--enable-metrics=true --enable-profiling=false`) and watch Zipkin (`http://localhost:9411`).
- Add integration tests with `pytest` + `asyncio` that launch both Dapr apps via `subprocess` to validate human approval path.
