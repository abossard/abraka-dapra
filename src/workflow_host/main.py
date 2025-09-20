"""Entrypoint for coordinating the Snacktopus workflow runtime."""

from __future__ import annotations

from dapr.ext.workflow import WorkflowRuntime


def build_runtime() -> WorkflowRuntime:
    """Create the workflow runtime instance without registering workflows yet."""
    runtime = WorkflowRuntime()
    # TODO: register workflows and activities once implementations land.
    return runtime


def main() -> None:
    """Bootstrap the Dapr Workflow runtime for Operation Snacktopus."""
    runtime = build_runtime()
    runtime.start()
    runtime.wait_for_shutdown()


if __name__ == "__main__":
    main()
