"""Instrument all outgoing HTTP requests made via ``urllib3`` and ``httpx``.

Monkey-patches :meth:`urllib3.connectionpool.HTTPConnectionPool.urlopen`,
:meth:`httpx.Client.send`, and :meth:`httpx.AsyncClient.send` so that every
outgoing HTTP call is logged with its method, URL, status code, and wall-clock
duration.

Because ``requests``, ``boto3``, and most Python HTTP clients use ``urllib3``
under the hood, the urllib3 patch captures the majority of outgoing HTTP
traffic. The httpx patch captures traffic from ``httpx``-based clients.

These patches coexist safely with other instrumentation libraries (e.g. Sentry)
because each patch wraps whatever function is already installed via a closure.

Query parameter values are redacted from logged URLs to prevent leaking API
keys, tokens, or PII into log aggregation systems.

Call :func:`install` once at app startup (e.g. in ``AppConfig.ready``).
"""

from __future__ import annotations

from typing import Any
import threading
import time
import urllib.parse
import uuid

import structlog

from ..conf import config as instrumentation_config

logger = structlog.get_logger(__name__)

_new_uuid = uuid.uuid7 if hasattr(uuid, "uuid7") else uuid.uuid4

_installed_urllib3 = False
_installed_httpx = False

_DEFAULT_PORTS: dict[str, int] = {
    "http": 80,
    "https": 443,
}


def _build_url(scheme: str, host: str, port: int | None, path: str) -> str:
    """Reconstruct the full URL from pool attributes and the request path.

    When urllib3 is used through an HTTP proxy (no CONNECT tunnel), the path is
    already an absolute URL — in that case, return it unchanged.
    """
    if path.startswith(("http://", "https://")):
        return path
    default_port = _DEFAULT_PORTS.get(scheme)
    if port is None or port == default_port:
        return f"{scheme}://{host}{path}"
    return f"{scheme}://{host}:{port}{path}"


def _redact_url(url: str) -> str:
    """Replace query parameter values with [REDACTED]."""
    parsed = urllib.parse.urlsplit(url)
    if not parsed.query:
        return url
    params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    redacted = urllib.parse.urlencode([(k, "REDACTED") for k, _ in params])
    return urllib.parse.urlunsplit(parsed._replace(query=redacted))


def _ns_to_ms(ns: int) -> float:
    return round(ns / 1_000_000.0, 2)


def _is_excluded(host: str) -> bool:
    """Check if the host is in the configured exclude list."""
    exclude_hosts = instrumentation_config.outgoing_http_exclude_hosts
    return host in exclude_hosts


def _make_common(
    *,
    method: str,
    url: str,
    host: str,
    request_id: str,
    proxy: bool | None = None,
) -> dict[str, object]:
    thread = threading.current_thread()
    common: dict[str, object] = dict(
        outgoing_http_request_id=request_id,
        outgoing_http_method=method,
        outgoing_http_url=url,
        outgoing_http_host=host,
        thread_name=thread.name,
    )
    if proxy is not None:
        common["outgoing_http_proxy"] = proxy
    return common


# ---------------------------------------------------------------------------
# urllib3
# ---------------------------------------------------------------------------


def _install_urllib3() -> None:
    global _installed_urllib3
    if _installed_urllib3:
        return

    try:
        import urllib3.connectionpool
        import urllib3.response
    except ImportError:
        return

    _original_urlopen = urllib3.connectionpool.HTTPConnectionPool.urlopen

    def _instrumented_urlopen(
        self: urllib3.connectionpool.HTTPConnectionPool,
        method: str,
        url: str,
        *args: Any,
        **kwargs: Any,
    ) -> urllib3.response.BaseHTTPResponse:
        if _is_excluded(self.host):
            return _original_urlopen(self, method, url, *args, **kwargs)

        full_url = _redact_url(_build_url(self.scheme, self.host, self.port, url))
        request_id = str(_new_uuid())
        uses_proxy = getattr(self, "proxy", None) is not None

        common = _make_common(
            method=method,
            url=full_url,
            host=self.host,
            proxy=uses_proxy,
            request_id=request_id,
        )
        logger.info("outgoing_http_request.start", **common)

        start_ns = time.perf_counter_ns()
        try:
            response = _original_urlopen(self, method, url, *args, **kwargs)
        except Exception as exc:
            duration_ms = _ns_to_ms(time.perf_counter_ns() - start_ns)
            logger.warning(
                "outgoing_http_request.done",
                **common,
                outgoing_http_status=None,
                duration_ms=duration_ms,
                success=False,
                error=type(exc).__name__,
            )
            raise

        duration_ms = _ns_to_ms(time.perf_counter_ns() - start_ns)
        success = 200 <= response.status < 400
        log = logger.info if success else logger.warning
        log(
            "outgoing_http_request.done",
            **common,
            outgoing_http_status=response.status,
            duration_ms=duration_ms,
            success=success,
        )
        return response

    urllib3.connectionpool.HTTPConnectionPool.urlopen = _instrumented_urlopen  # type: ignore[method-assign]
    _installed_urllib3 = True


# ---------------------------------------------------------------------------
# httpx
# ---------------------------------------------------------------------------


def _install_httpx() -> None:
    global _installed_httpx
    if _installed_httpx:
        return

    try:
        import httpx
    except ImportError:
        return

    _original_send = httpx.Client.send
    _original_async_send = httpx.AsyncClient.send

    def _instrumented_send(
        self: httpx.Client,
        request: httpx.Request,
        **kwargs: Any,
    ) -> httpx.Response:
        host = request.url.host
        if _is_excluded(host):
            return _original_send(self, request, **kwargs)

        url = _redact_url(str(request.url))
        request_id = str(_new_uuid())

        common = _make_common(
            method=request.method,
            url=url,
            host=host,
            request_id=request_id,
        )
        logger.info("outgoing_http_request.start", **common)

        start_ns = time.perf_counter_ns()
        try:
            response = _original_send(self, request, **kwargs)
        except Exception as exc:
            duration_ms = _ns_to_ms(time.perf_counter_ns() - start_ns)
            logger.warning(
                "outgoing_http_request.done",
                **common,
                outgoing_http_status=None,
                duration_ms=duration_ms,
                success=False,
                error=type(exc).__name__,
            )
            raise

        duration_ms = _ns_to_ms(time.perf_counter_ns() - start_ns)
        success = 200 <= response.status_code < 400
        log = logger.info if success else logger.warning
        log(
            "outgoing_http_request.done",
            **common,
            outgoing_http_status=response.status_code,
            duration_ms=duration_ms,
            success=success,
        )
        return response

    async def _instrumented_async_send(
        self: httpx.AsyncClient,
        request: httpx.Request,
        **kwargs: Any,
    ) -> httpx.Response:
        host = request.url.host
        if _is_excluded(host):
            return await _original_async_send(self, request, **kwargs)

        url = _redact_url(str(request.url))
        request_id = str(_new_uuid())

        common = _make_common(
            method=request.method,
            url=url,
            host=host,
            request_id=request_id,
        )
        logger.info("outgoing_http_request.start", **common)

        start_ns = time.perf_counter_ns()
        try:
            response = await _original_async_send(self, request, **kwargs)
        except Exception as exc:
            duration_ms = _ns_to_ms(time.perf_counter_ns() - start_ns)
            logger.warning(
                "outgoing_http_request.done",
                **common,
                outgoing_http_status=None,
                duration_ms=duration_ms,
                success=False,
                error=type(exc).__name__,
            )
            raise

        duration_ms = _ns_to_ms(time.perf_counter_ns() - start_ns)
        success = 200 <= response.status_code < 400
        log = logger.info if success else logger.warning
        log(
            "outgoing_http_request.done",
            **common,
            outgoing_http_status=response.status_code,
            duration_ms=duration_ms,
            success=success,
        )
        return response

    httpx.Client.send = _instrumented_send  # type: ignore[method-assign]
    httpx.AsyncClient.send = _instrumented_async_send  # type: ignore[method-assign]
    _installed_httpx = True


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def install() -> None:
    """Install instrumentation for all supported HTTP libraries.

    Patches ``urllib3`` and ``httpx`` (if installed). Safe to call multiple
    times; each library is only patched once.
    """
    _install_urllib3()
    _install_httpx()
