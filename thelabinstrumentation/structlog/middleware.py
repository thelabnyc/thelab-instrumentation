from collections.abc import Callable

from django.http import HttpRequest, HttpResponse
import structlog.contextvars

from ..conf import config


class HeaderBindingMiddleware:
    """Bind configured request headers to structlog contextvars."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        headers = config.structlog_request_headers
        bindings: dict[str, str] = {}
        for header_name, context_key in headers.items():
            meta_key = "HTTP_" + header_name.upper().replace("-", "_")
            value = request.META.get(meta_key, "")
            bindings[context_key] = value
        if bindings:
            structlog.contextvars.bind_contextvars(**bindings)
        return self.get_response(request)
