"""Telemetry utilities for Zipkin/OpenTelemetry integration."""

from contextlib import contextmanager
from typing import Generator


@contextmanager
def traced_span(name: str) -> Generator[None, None, None]:
    """Placeholder context manager for span instrumentation."""
    # TODO: Hook into OpenTelemetry once tracing backend is wired.
    yield
