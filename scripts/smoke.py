#!/usr/bin/env python
"""High-signal, low-noise smoke test runner for Abraka-Dapra.

Design principles (Grokking Simplicity / deep modules):
- Each check is a pure function returning a Result (no print side-effects inside check logic)
- Orchestration (formatting, coloring, timing) handled centrally
- Clear contract: name, status(bool), detail (short), diagnostics (optional long)

Run with: `uv run python scripts/smoke.py` (or `make smoke` after adding the target)
Requires the multi-app Dapr bundle running (or individual sidecars) and Redis.
"""
from __future__ import annotations

import json
import os
import time
import subprocess
import dataclasses as dc
from typing import Callable, List, Optional, Dict

import http.client

GREEN = "\x1b[32m"
RED = "\x1b[31m"
YELLOW = "\x1b[33m"
CYAN = "\x1b[36m"
DIM = "\x1b[2m"
RESET = "\x1b[0m"

AGENT_PORT = int(os.environ.get("AGENT_HTTP_PORT", "8000"))
# Sidecar ports may vary (multi-app ordering, concurrent runs). We'll attempt discovery via `dapr list -o json`.
AGENT_SIDECAR_PORT = None  # type: Optional[int]
WF_SIDECAR_PORT = None     # type: Optional[int]
TIMEOUT = 2  # seconds per HTTP call

@dc.dataclass
class Result:
    name: str
    ok: bool
    detail: str
    diagnostics: Optional[str] = None
    duration_ms: int = 0


def _http_get(port: int, path: str) -> tuple[int, str, dict]:
    conn = http.client.HTTPConnection("localhost", port, timeout=TIMEOUT)
    try:
        conn.request("GET", path)
        resp = conn.getresponse()
        body = resp.read().decode("utf-8", errors="replace")
        return resp.status, body, dict(resp.getheaders())
    finally:
        conn.close()


def _http_post(port: int, path: str, payload: str, headers: Optional[dict] = None) -> tuple[int, str]:
    conn = http.client.HTTPConnection("localhost", port, timeout=TIMEOUT)
    try:
        hdrs = {"Content-Type": "application/json"}
        if headers:
            hdrs.update(headers)
        conn.request("POST", path, body=payload, headers=hdrs)
        resp = conn.getresponse()
        body = resp.read().decode("utf-8", errors="replace")
        return resp.status, body
    finally:
        conn.close()

# ---- Checks ---- #

def check_agent_health() -> Result:
    start = time.time()
    try:
        status, body, _ = _http_get(AGENT_PORT, "/healthz")
        ok = status == 200 and '"status":"ok"' in body.replace(" ", "")
        return Result("agent:health", ok, f"HTTP {status}", body if not ok else None, int((time.time()-start)*1000))
    except Exception as e:  # noqa: BLE001
        return Result("agent:health", False, "exception", repr(e), int((time.time()-start)*1000))

def check_agent_root() -> Result:
    start = time.time()
    try:
        status, body, _ = _http_get(AGENT_PORT, "/")
        ok = status == 200 and "Snacktopus" in body
        return Result("agent:root", ok, f"HTTP {status}", body if not ok else None, int((time.time()-start)*1000))
    except Exception as e:  # noqa: BLE001
        return Result("agent:root", False, "exception", repr(e), int((time.time()-start)*1000))

def check_agent_metadata() -> Result:
    start = time.time()
    try:
        if AGENT_SIDECAR_PORT is None:
            return Result("dapr:agent:metadata", False, "sidecar_port_unknown", "call discover_ports first", int((time.time()-start)*1000))
        status, body, _ = _http_get(AGENT_SIDECAR_PORT, "/v1.0/metadata")
        if status != 200:
            return Result("dapr:agent:metadata", False, f"HTTP {status}", body, int((time.time()-start)*1000))
        data = json.loads(body)
        comp_names = {c["name"] for c in data.get("components", [])}
        required = {"statestore", "events"}
        missing = required - comp_names
        ok = not missing
        detail = f"components={sorted(comp_names)}"
        diag = None if ok else f"missing={sorted(missing)} raw={body[:400]}"
        return Result("dapr:agent:metadata", ok, detail, diag, int((time.time()-start)*1000))
    except Exception as e:  # noqa: BLE001
        return Result("dapr:agent:metadata", False, "exception", repr(e), int((time.time()-start)*1000))

def check_state_roundtrip() -> Result:
    start = time.time()
    key = "smoke:key"
    try:
        if AGENT_SIDECAR_PORT is None:
            return Result("dapr:state:roundtrip", False, "sidecar_port_unknown", None, int((time.time()-start)*1000))
        status, _ = _http_post(AGENT_SIDECAR_PORT, "/v1.0/state/statestore", json.dumps([{"key": key, "value": {"ok": True}}]))
        if status not in (200, 204):
            return Result("dapr:state:write", False, f"HTTP {status}", None, int((time.time()-start)*1000))
        status2, body2, _ = _http_get(AGENT_SIDECAR_PORT, f"/v1.0/state/statestore/{key}")
        ok = status2 == 200 and '"ok":true' in body2.replace(" ", "").lower()
        det = f"write={status} read={status2}"
        diag = body2 if not ok else None
        return Result("dapr:state:roundtrip", ok, det, diag, int((time.time()-start)*1000))
    except Exception as e:  # noqa: BLE001
        return Result("dapr:state:roundtrip", False, "exception", repr(e), int((time.time()-start)*1000))

def check_pubsub_publish() -> Result:
    start = time.time()
    try:
        if AGENT_SIDECAR_PORT is None:
            return Result("dapr:pubsub:publish", False, "sidecar_port_unknown", None, int((time.time()-start)*1000))
        status, body = _http_post(AGENT_SIDECAR_PORT, "/v1.0/publish/events/smoke.topic", json.dumps({"ping": "pong"}))
        ok = status in (200, 204)
        return Result("dapr:pubsub:publish", ok, f"HTTP {status}", body if not ok else None, int((time.time()-start)*1000))
    except Exception as e:  # noqa: BLE001
        return Result("dapr:pubsub:publish", False, "exception", repr(e), int((time.time()-start)*1000))

def check_secret_fetch() -> Result:
    start = time.time()
    try:
        if AGENT_SIDECAR_PORT is None:
            return Result("dapr:secret:get", False, "sidecar_port_unknown", None, int((time.time()-start)*1000))
        status, body, _ = _http_get(AGENT_SIDECAR_PORT, "/v1.0/secrets/localsecret/ollama")
        if status != 200:
            return Result("dapr:secret:get", False, f"HTTP {status}", body, int((time.time()-start)*1000))
        ok = 'apiKey' in body
        return Result("dapr:secret:get", ok, f"HTTP {status}", body if not ok else None, int((time.time()-start)*1000))
    except Exception as e:  # noqa: BLE001
        return Result("dapr:secret:get", False, "exception", repr(e), int((time.time()-start)*1000))

def check_workflow_start_and_status() -> Result:
    start = time.time()
    instance_id = "smoke-wf-1"
    try:
        if WF_SIDECAR_PORT is None:
            return Result("dapr:workflow:status", False, "workflow_sidecar_port_unknown", None, int((time.time()-start)*1000))
        # Start
        status_start, _ = _http_post(WF_SIDECAR_PORT, f"/v1.0-alpha1/workflows/dapr/hello_snacktopus/start?instanceID={instance_id}", "{}")
        if status_start not in (202, 200):
            return Result("dapr:workflow:start", False, f"start HTTP {status_start}", None, int((time.time()-start)*1000))
        # Poll (simple sleep; minimal logic)
        time.sleep(0.4)
        status_query, body_query, _ = _http_get(WF_SIDECAR_PORT, f"/v1.0-alpha1/workflows/dapr/instances/{instance_id}")
        if status_query != 200:
            return Result("dapr:workflow:status", False, f"query HTTP {status_query}", body_query, int((time.time()-start)*1000))
        data = json.loads(body_query)
        ok = data.get("runtimeStatus") == "COMPLETED" and "Workflow says hi" in (data.get("output") or "")
        return Result("dapr:workflow:status", ok, data.get("runtimeStatus", "?"), None if ok else body_query, int((time.time()-start)*1000))
    except Exception as e:  # noqa: BLE001
        return Result("dapr:workflow:status", False, "exception", repr(e), int((time.time()-start)*1000))

def discover_ports() -> Dict[str, int]:
    """Attempt to discover sidecar HTTP ports via `dapr list -o json`.

    Returns a mapping {appID: httpPort}. Leaves globals updated if found.
    """
    global AGENT_SIDECAR_PORT, WF_SIDECAR_PORT  # noqa: PLW0603
    try:
        raw = subprocess.check_output(["dapr", "list", "-o", "json"], text=True, timeout=3)
        data = json.loads(raw)
        mapping: Dict[str, int] = {}
        for entry in data:
            app_id = entry.get("appId") or entry.get("appID")
            http_port = entry.get("httpPort") or entry.get("httpEndpoint")
            if isinstance(http_port, str) and http_port.isdigit():
                http_port = int(http_port)
            if app_id and isinstance(http_port, int):
                mapping[app_id] = http_port
        if "agent-shell" in mapping:
            AGENT_SIDECAR_PORT = mapping["agent-shell"]
        if "workflow-host" in mapping:
            WF_SIDECAR_PORT = mapping["workflow-host"]
        return mapping
    except Exception:  # noqa: BLE001
        return {}

CHECKS: List[Callable[[], Result]] = [
    check_agent_health,
    check_agent_root,
    check_agent_metadata,
    check_state_roundtrip,
    check_pubsub_publish,
    check_secret_fetch,
    check_workflow_start_and_status,
]


def main() -> int:
    print(f"{CYAN}Abraka-Dapra Smoke Tests{RESET}")
    port_map = discover_ports()
    print(f"{DIM}discovered sidecar ports: {port_map or 'NONE'}{RESET}")
    if AGENT_SIDECAR_PORT is None:
        print(f"{YELLOW}WARN{RESET} could not determine agent-shell sidecar port (attempted discovery). Override with AGENT_SIDECAR_PORT env var.")
    if WF_SIDECAR_PORT is None:
        print(f"{YELLOW}WARN{RESET} could not determine workflow-host sidecar port. Override with WORKFLOW_SIDECAR_PORT env var.")
    results: List[Result] = []
    start_suite = time.time()
    for fn in CHECKS:
        res = fn()
        results.append(res)
        color = GREEN if res.ok else RED
        sym = "✔" if res.ok else "✘"
        print(f" {color}{sym}{RESET} {res.name:<24} {res.detail:<32} {DIM}{res.duration_ms}ms{RESET}")
        if res.diagnostics and not res.ok:
            print(f"   {YELLOW}diag:{RESET} {res.diagnostics}")
    duration = int((time.time()-start_suite)*1000)
    passed = sum(1 for r in results if r.ok)
    total = len(results)
    status_color = GREEN if passed == total else (YELLOW if passed >= total/2 else RED)
    print()
    print(f"{status_color}Summary:{RESET} {passed}/{total} passed in {duration}ms")
    # Suggest remediation quickly
    failing = [r for r in results if not r.ok]
    if failing:
        print(f"{RED}Failures:{RESET}")
        for r in failing:
            print(f" - {r.name}: {r.detail}")
        # Provide contextual hints
        if any(f.detail.startswith("sidecar_port_unknown") for f in failing):
            print("  Hint: Run `dapr list -o json` to verify sidecar ports; export AGENT_SIDECAR_PORT / WORKFLOW_SIDECAR_PORT if ordering changed.")
        if any("ConnectionRefusedError" in (f.diagnostics or "") for f in failing):
            print("  Hint: Ensure non-slim init (placement, redis) and the multi-app manifest are running. Try: `dapr init` (non-slim) then `dapr run -f manifests`.")
    return 0 if passed == total else 1

if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
