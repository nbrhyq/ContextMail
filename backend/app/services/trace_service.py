from time import perf_counter
from typing import Callable, TypeVar

from app.models.domain import TraceEvent


T = TypeVar("T")


def traced(actor: str, action: str, callback: Callable[[], T]):
    started = perf_counter()
    try:
        result = callback()
        event = TraceEvent(
            actor=actor,
            action=action,
            status="COMPLETED",
            summary=f"{actor} completed {action}",
            latency_ms=int((perf_counter() - started) * 1000),
        )
        return result, event
    except Exception as exc:
        event = TraceEvent(
            actor=actor,
            action=action,
            status="FAILED",
            summary=str(exc),
            latency_ms=int((perf_counter() - started) * 1000),
        )
        raise RuntimeError(event.model_dump_json()) from exc

