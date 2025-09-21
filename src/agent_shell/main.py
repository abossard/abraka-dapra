"""Entrypoint for the Snacktopus agent shell FastAPI application."""

from fastapi import FastAPI

app = FastAPI(title="Operation Snacktopus Agent Shell")


@app.get("/")
async def root() -> dict[str, str]:
    """Minimal hello-world response for smoke testing."""
    return {"message": "Snacktopus agent says hello."}


@app.get("/healthz")
async def healthcheck() -> dict[str, str]:
    """Lightweight readiness probe for local dev."""
    return {"status": "ok"}
