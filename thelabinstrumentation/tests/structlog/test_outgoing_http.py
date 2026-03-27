from __future__ import annotations

from unittest.mock import MagicMock, patch
import asyncio

from django.test import SimpleTestCase, override_settings
import httpx
import urllib3.connectionpool
import urllib3.exceptions
import urllib3.response

from ...structlog import outgoing_http


class BuildUrlTest(SimpleTestCase):
    """Tests for the _build_url helper."""

    def test_https_default_port(self) -> None:
        self.assertEqual(
            outgoing_http._build_url("https", "api.example.com", 443, "/v1/items"),
            "https://api.example.com/v1/items",
        )

    def test_http_default_port(self) -> None:
        self.assertEqual(
            outgoing_http._build_url("http", "api.example.com", 80, "/v1/items"),
            "http://api.example.com/v1/items",
        )

    def test_non_default_port(self) -> None:
        self.assertEqual(
            outgoing_http._build_url("http", "localhost", 8080, "/path"),
            "http://localhost:8080/path",
        )

    def test_none_port_omitted(self) -> None:
        self.assertEqual(
            outgoing_http._build_url("https", "api.example.com", None, "/v1"),
            "https://api.example.com/v1",
        )

    def test_preserves_query_string(self) -> None:
        self.assertEqual(
            outgoing_http._build_url(
                "https", "api.example.com", 443, "/v1/items?key=val"
            ),
            "https://api.example.com/v1/items?key=val",
        )

    def test_absolute_url_returned_as_is(self) -> None:
        """When using an HTTP proxy, urllib3 passes the full URL."""
        self.assertEqual(
            outgoing_http._build_url(
                "http",
                "proxy.local",
                3128,
                "http://api.example.com/v1/items",
            ),
            "http://api.example.com/v1/items",
        )


class RedactUrlTest(SimpleTestCase):
    """Tests for the _redact_url helper."""

    def test_no_query_string_unchanged(self) -> None:
        self.assertEqual(
            outgoing_http._redact_url("https://api.example.com/v1/items"),
            "https://api.example.com/v1/items",
        )

    def test_single_param_redacted(self) -> None:
        self.assertEqual(
            outgoing_http._redact_url("https://api.example.com/v1?secret=abc"),
            "https://api.example.com/v1?secret=REDACTED",
        )

    def test_multiple_params_redacted(self) -> None:
        result = outgoing_http._redact_url(
            "https://api.example.com/v1?key=abc&page=2&token=xyz"
        )
        self.assertEqual(
            result,
            "https://api.example.com/v1?key=REDACTED&page=REDACTED&token=REDACTED",
        )

    def test_empty_value_redacted(self) -> None:
        self.assertEqual(
            outgoing_http._redact_url("https://example.com/v1?flag="),
            "https://example.com/v1?flag=REDACTED",
        )

    def test_fragment_preserved(self) -> None:
        result = outgoing_http._redact_url("https://example.com/v1?key=val#section")
        self.assertIn("#section", result)
        self.assertNotIn("val", result)

    def test_path_only_unchanged(self) -> None:
        self.assertEqual(
            outgoing_http._redact_url("/v1/items"),
            "/v1/items",
        )

    def test_relative_path_with_query_redacted(self) -> None:
        """urllib3 passes relative paths which may include query strings."""
        self.assertEqual(
            outgoing_http._redact_url("/v1/items?secret=abc"),
            "/v1/items?secret=REDACTED",
        )


# ---------------------------------------------------------------------------
# urllib3 tests
# ---------------------------------------------------------------------------


class Urllib3InstallIdempotencyTest(SimpleTestCase):
    """Tests that install() is safe to call multiple times for urllib3."""

    def setUp(self) -> None:
        self._saved_urlopen = urllib3.connectionpool.HTTPConnectionPool.urlopen
        outgoing_http._installed_urllib3 = False

    def tearDown(self) -> None:
        urllib3.connectionpool.HTTPConnectionPool.urlopen = self._saved_urlopen  # type: ignore[method-assign]
        outgoing_http._installed_urllib3 = False

    def test_install_is_idempotent(self) -> None:
        outgoing_http.install()
        first = urllib3.connectionpool.HTTPConnectionPool.urlopen
        outgoing_http.install()
        second = urllib3.connectionpool.HTTPConnectionPool.urlopen
        self.assertIs(first, second)


class Urllib3LoggingTest(SimpleTestCase):
    """Tests for the instrumented urllib3 urlopen."""

    def setUp(self) -> None:
        self._saved_urlopen = urllib3.connectionpool.HTTPConnectionPool.urlopen
        outgoing_http._installed_urllib3 = False

    def tearDown(self) -> None:
        urllib3.connectionpool.HTTPConnectionPool.urlopen = self._saved_urlopen  # type: ignore[method-assign]
        outgoing_http._installed_urllib3 = False

    def _install_with_fake_urlopen(self, fake_urlopen: MagicMock) -> None:
        """Patch HTTPConnectionPool.urlopen with fake, then install instrumentation."""
        urllib3.connectionpool.HTTPConnectionPool.urlopen = fake_urlopen  # type: ignore[method-assign]
        outgoing_http.install()

    def _make_pool(
        self,
        host: str = "api.example.com",
        port: int = 443,
        scheme: str = "https",
    ) -> urllib3.HTTPSConnectionPool:
        """Create a pool without actually connecting."""
        pool = urllib3.HTTPSConnectionPool(host=host, port=port)
        pool.scheme = scheme
        return pool

    @patch.object(outgoing_http, "logger")
    def test_successful_request_logs_start_and_done(
        self, mock_logger: MagicMock
    ) -> None:
        fake_response = MagicMock(spec=urllib3.response.HTTPResponse)
        fake_response.status = 200
        fake_urlopen = MagicMock(return_value=fake_response)

        self._install_with_fake_urlopen(fake_urlopen)
        pool = self._make_pool()
        result = pool.urlopen("GET", "/v1/items?secret=abc")

        self.assertEqual(result, fake_response)
        self.assertEqual(mock_logger.info.call_count, 2)

        start_kw = mock_logger.info.call_args_list[0][1]
        self.assertEqual(start_kw["outgoing_http_method"], "GET")
        # Query param values must be redacted
        self.assertIn("secret=REDACTED", start_kw["outgoing_http_url"])
        self.assertNotIn("abc", start_kw["outgoing_http_url"])
        self.assertEqual(start_kw["outgoing_http_host"], "api.example.com")
        self.assertIn("outgoing_http_request_id", start_kw)
        self.assertIn("thread_name", start_kw)

        done_kw = mock_logger.info.call_args_list[1][1]
        self.assertEqual(done_kw["outgoing_http_status"], 200)
        self.assertTrue(done_kw["success"])
        self.assertIsInstance(done_kw["duration_ms"], float)

        self.assertEqual(
            start_kw["outgoing_http_request_id"],
            done_kw["outgoing_http_request_id"],
        )

    @patch.object(outgoing_http, "logger")
    def test_server_error_logs_warning(self, mock_logger: MagicMock) -> None:
        fake_response = MagicMock(spec=urllib3.response.HTTPResponse)
        fake_response.status = 502
        fake_urlopen = MagicMock(return_value=fake_response)

        self._install_with_fake_urlopen(fake_urlopen)
        pool = self._make_pool()
        pool.urlopen("POST", "/api/tax")

        mock_logger.info.assert_called_once()
        mock_logger.warning.assert_called_once()
        done_kw = mock_logger.warning.call_args[1]
        self.assertEqual(done_kw["outgoing_http_status"], 502)
        self.assertFalse(done_kw["success"])

    @patch.object(outgoing_http, "logger")
    def test_4xx_status_logs_warning(self, mock_logger: MagicMock) -> None:
        fake_response = MagicMock(spec=urllib3.response.HTTPResponse)
        fake_response.status = 404
        fake_urlopen = MagicMock(return_value=fake_response)

        self._install_with_fake_urlopen(fake_urlopen)
        pool = self._make_pool()
        pool.urlopen("GET", "/missing")

        mock_logger.info.assert_called_once()
        mock_logger.warning.assert_called_once()
        done_kw = mock_logger.warning.call_args[1]
        self.assertFalse(done_kw["success"])
        self.assertEqual(done_kw["outgoing_http_status"], 404)

    @patch.object(outgoing_http, "logger")
    def test_connection_error_logs_warning_and_reraises(
        self, mock_logger: MagicMock
    ) -> None:
        fake_urlopen = MagicMock(
            side_effect=urllib3.exceptions.NewConnectionError(
                MagicMock(), "Connection refused"
            ),
        )

        self._install_with_fake_urlopen(fake_urlopen)
        pool = self._make_pool(host="down.example.com")
        with self.assertRaises(urllib3.exceptions.NewConnectionError):
            pool.urlopen("GET", "/health")

        mock_logger.info.assert_called_once()
        mock_logger.warning.assert_called_once()
        done_kw = mock_logger.warning.call_args[1]
        self.assertIsNone(done_kw["outgoing_http_status"])
        self.assertFalse(done_kw["success"])
        self.assertEqual(done_kw["error"], "NewConnectionError")
        # error_detail should NOT be present (may contain sensitive info)
        self.assertNotIn("error_detail", done_kw)

    @patch.object(outgoing_http, "logger")
    def test_proxy_error_tagged_distinctly(self, mock_logger: MagicMock) -> None:
        fake_urlopen = MagicMock(
            side_effect=urllib3.exceptions.ProxyError("proxy refused", MagicMock()),
        )

        self._install_with_fake_urlopen(fake_urlopen)
        pool = self._make_pool()
        pool.proxy = MagicMock()
        with self.assertRaises(urllib3.exceptions.ProxyError):
            pool.urlopen("POST", "/api/tax")

        done_kw = mock_logger.warning.call_args[1]
        self.assertEqual(done_kw["error"], "ProxyError")
        self.assertTrue(done_kw["outgoing_http_proxy"])

    @patch.object(outgoing_http, "logger")
    def test_timeout_error_logs_warning_and_reraises(
        self, mock_logger: MagicMock
    ) -> None:
        fake_urlopen = MagicMock(
            side_effect=urllib3.exceptions.ReadTimeoutError(
                MagicMock(), "https://slow.example.com", "timed out"
            ),
        )

        self._install_with_fake_urlopen(fake_urlopen)
        pool = self._make_pool(host="slow.example.com")
        with self.assertRaises(urllib3.exceptions.ReadTimeoutError):
            pool.urlopen("GET", "/data")

        done_kw = mock_logger.warning.call_args[1]
        self.assertEqual(done_kw["error"], "ReadTimeoutError")

    @patch.object(outgoing_http, "logger")
    def test_proxy_detected_from_pool(self, mock_logger: MagicMock) -> None:
        fake_response = MagicMock(spec=urllib3.response.HTTPResponse)
        fake_response.status = 200
        fake_urlopen = MagicMock(return_value=fake_response)

        self._install_with_fake_urlopen(fake_urlopen)
        pool = self._make_pool()
        pool.proxy = MagicMock()
        pool.urlopen("GET", "/v1")

        start_kw = mock_logger.info.call_args_list[0][1]
        self.assertTrue(start_kw["outgoing_http_proxy"])

    @patch.object(outgoing_http, "logger")
    def test_no_proxy_when_none(self, mock_logger: MagicMock) -> None:
        fake_response = MagicMock(spec=urllib3.response.HTTPResponse)
        fake_response.status = 200
        fake_urlopen = MagicMock(return_value=fake_response)

        self._install_with_fake_urlopen(fake_urlopen)
        pool = self._make_pool()
        pool.urlopen("GET", "/v1")

        start_kw = mock_logger.info.call_args_list[0][1]
        self.assertFalse(start_kw["outgoing_http_proxy"])

    @patch.object(outgoing_http, "logger")
    def test_non_default_port_in_url(self, mock_logger: MagicMock) -> None:
        fake_response = MagicMock(spec=urllib3.response.HTTPResponse)
        fake_response.status = 200
        fake_urlopen = MagicMock(return_value=fake_response)

        self._install_with_fake_urlopen(fake_urlopen)
        pool = self._make_pool(host="localhost", port=8080, scheme="http")
        pool.urlopen("GET", "/health")

        start_kw = mock_logger.info.call_args_list[0][1]
        self.assertEqual(start_kw["outgoing_http_url"], "http://localhost:8080/health")

    @override_settings(
        THELAB_INSTRUMENTATION={
            "OUTGOING_HTTP_EXCLUDE_HOSTS": ["health.internal", "localhost"],
        }
    )
    @patch.object(outgoing_http, "logger")
    def test_excluded_host_skips_logging(self, mock_logger: MagicMock) -> None:
        fake_response = MagicMock(spec=urllib3.response.HTTPResponse)
        fake_response.status = 200
        fake_urlopen = MagicMock(return_value=fake_response)

        self._install_with_fake_urlopen(fake_urlopen)
        pool = self._make_pool(host="health.internal")
        result = pool.urlopen("GET", "/healthz")

        # Request goes through, but no logging
        self.assertEqual(result, fake_response)
        mock_logger.info.assert_not_called()
        mock_logger.warning.assert_not_called()

    @override_settings(
        THELAB_INSTRUMENTATION={
            "OUTGOING_HTTP_EXCLUDE_HOSTS": ["health.internal"],
        }
    )
    @patch.object(outgoing_http, "logger")
    def test_non_excluded_host_still_logged(self, mock_logger: MagicMock) -> None:
        fake_response = MagicMock(spec=urllib3.response.HTTPResponse)
        fake_response.status = 200
        fake_urlopen = MagicMock(return_value=fake_response)

        self._install_with_fake_urlopen(fake_urlopen)
        pool = self._make_pool(host="api.example.com")
        pool.urlopen("GET", "/v1")

        self.assertEqual(mock_logger.info.call_count, 2)


# ---------------------------------------------------------------------------
# httpx tests
# ---------------------------------------------------------------------------


class HttpxInstallIdempotencyTest(SimpleTestCase):
    """Tests that install() is safe to call multiple times for httpx."""

    def setUp(self) -> None:
        self._saved_send = httpx.Client.send
        self._saved_async_send = httpx.AsyncClient.send
        outgoing_http._installed_httpx = False

    def tearDown(self) -> None:
        httpx.Client.send = self._saved_send  # type: ignore[method-assign]
        httpx.AsyncClient.send = self._saved_async_send  # type: ignore[method-assign]
        outgoing_http._installed_httpx = False

    def test_install_is_idempotent(self) -> None:
        outgoing_http.install()
        first = httpx.Client.send
        outgoing_http.install()
        second = httpx.Client.send
        self.assertIs(first, second)


class HttpxLoggingTest(SimpleTestCase):
    """Tests for the instrumented httpx.Client.send."""

    def setUp(self) -> None:
        self._saved_send = httpx.Client.send
        self._saved_async_send = httpx.AsyncClient.send
        outgoing_http._installed_httpx = False

    def tearDown(self) -> None:
        httpx.Client.send = self._saved_send  # type: ignore[method-assign]
        httpx.AsyncClient.send = self._saved_async_send  # type: ignore[method-assign]
        outgoing_http._installed_httpx = False

    def _install_with_fake_send(self, fake_send: MagicMock) -> None:
        httpx.Client.send = fake_send  # type: ignore[method-assign]
        outgoing_http.install()

    @patch.object(outgoing_http, "logger")
    def test_successful_request_logs_start_and_done(
        self, mock_logger: MagicMock
    ) -> None:
        fake_response = MagicMock(spec=httpx.Response)
        fake_response.status_code = 200
        fake_send = MagicMock(return_value=fake_response)

        self._install_with_fake_send(fake_send)
        client = httpx.Client()
        request = httpx.Request("GET", "https://api.example.com/v1/items?key=val")
        result = client.send(request)

        self.assertEqual(result, fake_response)
        self.assertEqual(mock_logger.info.call_count, 2)

        start_kw = mock_logger.info.call_args_list[0][1]
        self.assertEqual(start_kw["outgoing_http_method"], "GET")
        # Query param values must be redacted
        self.assertIn("key=REDACTED", start_kw["outgoing_http_url"])
        self.assertNotIn("val", start_kw["outgoing_http_url"])
        self.assertEqual(start_kw["outgoing_http_host"], "api.example.com")
        self.assertIn("outgoing_http_request_id", start_kw)
        # httpx logs should NOT include proxy field
        self.assertNotIn("outgoing_http_proxy", start_kw)

        done_kw = mock_logger.info.call_args_list[1][1]
        self.assertEqual(done_kw["outgoing_http_status"], 200)
        self.assertTrue(done_kw["success"])
        self.assertIsInstance(done_kw["duration_ms"], float)

        self.assertEqual(
            start_kw["outgoing_http_request_id"],
            done_kw["outgoing_http_request_id"],
        )

    @patch.object(outgoing_http, "logger")
    def test_server_error_logs_warning(self, mock_logger: MagicMock) -> None:
        fake_response = MagicMock(spec=httpx.Response)
        fake_response.status_code = 502
        fake_send = MagicMock(return_value=fake_response)

        self._install_with_fake_send(fake_send)
        client = httpx.Client()
        request = httpx.Request("POST", "https://api.example.com/tax")
        client.send(request)

        mock_logger.info.assert_called_once()
        mock_logger.warning.assert_called_once()
        done_kw = mock_logger.warning.call_args[1]
        self.assertEqual(done_kw["outgoing_http_status"], 502)
        self.assertFalse(done_kw["success"])

    @patch.object(outgoing_http, "logger")
    def test_connect_error_logs_warning_and_reraises(
        self, mock_logger: MagicMock
    ) -> None:
        request = httpx.Request("GET", "https://down.example.com/health")
        fake_send = MagicMock(
            side_effect=httpx.ConnectError("Connection refused"),
        )

        self._install_with_fake_send(fake_send)
        client = httpx.Client()
        with self.assertRaises(httpx.ConnectError):
            client.send(request)

        mock_logger.info.assert_called_once()
        mock_logger.warning.assert_called_once()
        done_kw = mock_logger.warning.call_args[1]
        self.assertIsNone(done_kw["outgoing_http_status"])
        self.assertFalse(done_kw["success"])
        self.assertEqual(done_kw["error"], "ConnectError")

    @patch.object(outgoing_http, "logger")
    def test_timeout_error_logs_warning_and_reraises(
        self, mock_logger: MagicMock
    ) -> None:
        request = httpx.Request("GET", "https://slow.example.com/data")
        fake_send = MagicMock(
            side_effect=httpx.ReadTimeout("timed out"),
        )

        self._install_with_fake_send(fake_send)
        client = httpx.Client()
        with self.assertRaises(httpx.ReadTimeout):
            client.send(request)

        done_kw = mock_logger.warning.call_args[1]
        self.assertEqual(done_kw["error"], "ReadTimeout")

    @override_settings(
        THELAB_INSTRUMENTATION={
            "OUTGOING_HTTP_EXCLUDE_HOSTS": ["health.internal"],
        }
    )
    @patch.object(outgoing_http, "logger")
    def test_excluded_host_skips_logging(self, mock_logger: MagicMock) -> None:
        fake_response = MagicMock(spec=httpx.Response)
        fake_response.status_code = 200
        fake_send = MagicMock(return_value=fake_response)

        self._install_with_fake_send(fake_send)
        client = httpx.Client()
        request = httpx.Request("GET", "https://health.internal/healthz")
        result = client.send(request)

        self.assertEqual(result, fake_response)
        mock_logger.info.assert_not_called()


class AsyncHttpxLoggingTest(SimpleTestCase):
    """Tests for the instrumented httpx.AsyncClient.send."""

    def setUp(self) -> None:
        self._saved_send = httpx.Client.send
        self._saved_async_send = httpx.AsyncClient.send
        outgoing_http._installed_httpx = False

    def tearDown(self) -> None:
        httpx.Client.send = self._saved_send  # type: ignore[method-assign]
        httpx.AsyncClient.send = self._saved_async_send  # type: ignore[method-assign]
        outgoing_http._installed_httpx = False

    def _install_with_fake_send(self, fake_async_send: MagicMock) -> None:
        httpx.AsyncClient.send = fake_async_send  # type: ignore[method-assign]
        outgoing_http.install()

    @patch.object(outgoing_http, "logger")
    def test_async_successful_request_logs_start_and_done(
        self, mock_logger: MagicMock
    ) -> None:
        fake_response = MagicMock(spec=httpx.Response)
        fake_response.status_code = 200

        async def fake_async_send(
            self: httpx.AsyncClient, request: httpx.Request, **kwargs: object
        ) -> httpx.Response:
            return fake_response

        self._install_with_fake_send(fake_async_send)  # type: ignore[arg-type]

        async def _run() -> httpx.Response:
            client = httpx.AsyncClient()
            request = httpx.Request("GET", "https://api.example.com/v1")
            return await client.send(request)

        result = asyncio.run(_run())

        self.assertEqual(result, fake_response)
        self.assertEqual(mock_logger.info.call_count, 2)

        start_kw = mock_logger.info.call_args_list[0][1]
        self.assertEqual(start_kw["outgoing_http_method"], "GET")
        self.assertEqual(start_kw["outgoing_http_host"], "api.example.com")

        done_kw = mock_logger.info.call_args_list[1][1]
        self.assertEqual(done_kw["outgoing_http_status"], 200)
        self.assertTrue(done_kw["success"])

    @patch.object(outgoing_http, "logger")
    def test_async_error_logs_warning_and_reraises(
        self, mock_logger: MagicMock
    ) -> None:
        async def fake_async_send(
            self: httpx.AsyncClient, request: httpx.Request, **kwargs: object
        ) -> httpx.Response:
            raise httpx.ConnectError("Connection refused")

        self._install_with_fake_send(fake_async_send)  # type: ignore[arg-type]

        async def _run() -> None:
            client = httpx.AsyncClient()
            request = httpx.Request("GET", "https://down.example.com/health")
            await client.send(request)

        with self.assertRaises(httpx.ConnectError):
            asyncio.run(_run())

        mock_logger.warning.assert_called_once()
        done_kw = mock_logger.warning.call_args[1]
        self.assertIsNone(done_kw["outgoing_http_status"])
        self.assertEqual(done_kw["error"], "ConnectError")
