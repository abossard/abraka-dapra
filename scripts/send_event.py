"""CLI helper to raise saga events against the Snacktopus workflow."""

from __future__ import annotations

import asyncio
from typing import Optional

import typer

app = typer.Typer(help="Send human/ops/supply intake events to Snacktopus instances.")


@app.command()
def human(
    instance_id: str = typer.Argument(..., help="Workflow instance ID to target."),
    verdict: str = typer.Option("approved", help="Outcome to report (approved/rejected/timeout)."),
    notes: Optional[str] = typer.Option(None, help="Optional context from the reviewer."),
) -> None:
    """Stub command for delivering human approval decisions."""
    asyncio.run(_dispatch_event(instance_id, "humanApproval", {"verdict": verdict, "notes": notes}))


async def _dispatch_event(instance_id: str, event_name: str, payload: dict[str, Optional[str]]) -> None:
    """Placeholder for Dapr Workflow client interaction."""
    # TODO: Wire up Dapr Workflow client once workflow host is implemented.
    print(
        f"Would send event '{event_name}' to instance '{instance_id}' with payload {payload}.",
    )


if __name__ == "__main__":
    app()
