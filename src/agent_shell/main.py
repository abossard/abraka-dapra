"""Entrypoint for the Snacktopus agent shell FastAPI application."""

from fastapi import FastAPI

app = FastAPI(title="Operation Snacktopus Agent Shell")


@app.get("/healthz")
async def healthcheck() -> dict[str, str]:
    """Lightweight readiness probe for local dev."""
    return {"status": "ok"}
