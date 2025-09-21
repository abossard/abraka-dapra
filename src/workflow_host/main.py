"""Entrypoint for coordinating the Snacktopus workflow runtime."""

from __future__ import annotations

import logging
import signal
import threading
from typing import Optional

from dapr.ext.workflow import DaprWorkflowContext, WorkflowActivityContext, WorkflowRuntime

LOGGER = logging.getLogger("snacktopus.workflow")
RUNTIME = WorkflowRuntime()


@RUNTIME.workflow(name="hello_snacktopus")
def hello_snacktopus(ctx: DaprWorkflowContext, name: Optional[str] = None) -> str:
    """Minimal workflow returning a greeting so the runtime has a registered entrypoint."""
    guest = name or "Snacktopus"
    LOGGER.info("Workflow instance %s greeting %s", ctx.instance_id, guest)
    return f"Workflow says hi to {guest}!"


@RUNTIME.activity(name="echo")
def echo_activity(ctx: WorkflowActivityContext, payload: Optional[str] = None) -> str:
    """Simple activity that bounces its payload; useful for manual experimentation."""
    message = payload or "pong"
    LOGGER.debug("Echo activity invoked with %s", message)
    return message


def main() -> None:
    """Bootstrap the Dapr Workflow runtime for Operation Snacktopus."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
    LOGGER.info("Starting workflow runtime")
    RUNTIME.start()

    stop_event = threading.Event()

    def _graceful_shutdown(signum: int, _frame: object) -> None:
        LOGGER.info("Received signal %s; shutting down workflow runtime", signum)
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, _graceful_shutdown)

    try:
        stop_event.wait()
    finally:
        LOGGER.info("Stopping workflow runtime")
        RUNTIME.shutdown()
        LOGGER.info("Workflow runtime stopped")


if __name__ == "__main__":
    main()
