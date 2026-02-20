from unittest.mock import patch

from django.http import HttpRequest, HttpResponse
from django.test import SimpleTestCase, override_settings
import structlog.contextvars

from ...structlog.middleware import HeaderBindingMiddleware


class HeaderBindingMiddlewareTestCase(SimpleTestCase):
    """Test cases for HeaderBindingMiddleware."""

    def setUp(self) -> None:
        structlog.contextvars.clear_contextvars()

    def tearDown(self) -> None:
        structlog.contextvars.clear_contextvars()

    def _get_response(self, request: HttpRequest) -> HttpResponse:
        return HttpResponse("OK")

    def test_binds_headers_to_contextvars(self) -> None:
        """Test that configured headers are read from META and bound."""
        middleware = HeaderBindingMiddleware(self._get_response)
        request = HttpRequest()
        request.META["HTTP_X_AMZ_CF_ID"] = "abc123"
        request.META["HTTP_X_AMZN_TRACE_ID"] = "trace456"

        with patch.object(
            structlog.contextvars,
            "bind_contextvars",
            wraps=structlog.contextvars.bind_contextvars,
        ) as mock_bind:
            middleware(request)
            mock_bind.assert_called_once_with(
                cf_id="abc123", x_amzn_trace_id="trace456"
            )

    def test_missing_headers_default_to_empty_string(self) -> None:
        """Test that missing headers are bound as empty strings."""
        middleware = HeaderBindingMiddleware(self._get_response)
        request = HttpRequest()

        with patch.object(
            structlog.contextvars,
            "bind_contextvars",
            wraps=structlog.contextvars.bind_contextvars,
        ) as mock_bind:
            middleware(request)
            mock_bind.assert_called_once_with(cf_id="", x_amzn_trace_id="")

    @override_settings(
        THELAB_INSTRUMENTATION={
            "STRUCTLOG_REQUEST_HEADERS": {"x-custom": "custom_val"},
        }
    )
    def test_custom_header_config(self) -> None:
        """Test that custom header configuration is respected."""
        middleware = HeaderBindingMiddleware(self._get_response)
        request = HttpRequest()
        request.META["HTTP_X_CUSTOM"] = "hello"

        with patch.object(
            structlog.contextvars,
            "bind_contextvars",
            wraps=structlog.contextvars.bind_contextvars,
        ) as mock_bind:
            middleware(request)
            mock_bind.assert_called_once_with(custom_val="hello")

    def test_returns_response(self) -> None:
        """Test that the response from get_response is returned."""
        middleware = HeaderBindingMiddleware(self._get_response)
        request = HttpRequest()

        response = middleware(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"OK")
