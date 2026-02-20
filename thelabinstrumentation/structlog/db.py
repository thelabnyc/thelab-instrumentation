from collections.abc import Callable
from contextlib import ExitStack
from contextvars import ContextVar
from time import perf_counter_ns
from typing import Any

from django.db import connections
from django.http import HttpRequest, HttpResponse
import structlog.contextvars

_query_count: ContextVar[int] = ContextVar("_query_count", default=0)
_query_duration_ns: ContextVar[int] = ContextVar("_query_duration_ns", default=0)


def _query_stats_wrapper(
    execute: Callable[..., Any],
    sql: str,
    params: tuple[Any, ...] | None,
    many: bool,
    context: dict[str, Any],
) -> Any:
    start = perf_counter_ns()
    try:
        return execute(sql, params, many, context)
    finally:
        duration = perf_counter_ns() - start
        _query_count.set(_query_count.get(0) + 1)
        _query_duration_ns.set(_query_duration_ns.get(0) + duration)


class QueryStatsMiddleware:
    """Bind per-request DB query count and duration to structlog contextvars."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        _query_count.set(0)
        _query_duration_ns.set(0)

        try:
            with ExitStack() as stack:
                for conn in connections.all():
                    stack.enter_context(conn.execute_wrapper(_query_stats_wrapper))
                response = self.get_response(request)
        finally:
            duration_ms = round(_query_duration_ns.get(0) / 1_000_000, 2)
            structlog.contextvars.bind_contextvars(
                db_query_count=_query_count.get(0),
                db_query_duration_ms=duration_ms,
            )
        return response
