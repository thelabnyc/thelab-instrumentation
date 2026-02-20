from unittest.mock import patch

from django.db import connection
from django.http import HttpRequest, HttpResponse
from django.test import SimpleTestCase, TransactionTestCase
import structlog.contextvars

from ...structlog.db import (
    QueryStatsMiddleware,
    _query_count,
    _query_duration_ns,
    _query_stats_wrapper,
)


class QueryStatsWrapperTestCase(SimpleTestCase):
    """Test cases for the _query_stats_wrapper function."""

    def setUp(self) -> None:
        _query_count.set(0)
        _query_duration_ns.set(0)

    def tearDown(self) -> None:
        _query_count.set(0)
        _query_duration_ns.set(0)

    def test_counts_queries(self) -> None:
        """Test that the wrapper increments the query count."""
        call_count = 0

        def fake_execute(sql, params, many, context):  # type: ignore[no-untyped-def]
            nonlocal call_count
            call_count += 1
            return None

        _query_stats_wrapper(fake_execute, "SELECT 1", None, False, {})
        _query_stats_wrapper(fake_execute, "SELECT 2", None, False, {})

        self.assertEqual(_query_count.get(), 2)
        self.assertEqual(call_count, 2)

    def test_measures_duration(self) -> None:
        """Test that the wrapper accumulates duration."""

        def fake_execute(sql, params, many, context):  # type: ignore[no-untyped-def]
            return None

        _query_stats_wrapper(fake_execute, "SELECT 1", None, False, {})

        self.assertGreaterEqual(_query_duration_ns.get(), 0)

    def test_propagates_return_value(self) -> None:
        """Test that the wrapper returns the execute result."""

        def fake_execute(sql, params, many, context):  # type: ignore[no-untyped-def]
            return "result"

        result = _query_stats_wrapper(fake_execute, "SELECT 1", None, False, {})
        self.assertEqual(result, "result")

    def test_propagates_exception(self) -> None:
        """Test that the wrapper re-raises exceptions and still records stats."""

        def fake_execute(sql, params, many, context):  # type: ignore[no-untyped-def]
            raise ValueError("boom")

        with self.assertRaises(ValueError):
            _query_stats_wrapper(fake_execute, "SELECT 1", None, False, {})

        self.assertEqual(_query_count.get(), 1)
        self.assertGreater(_query_duration_ns.get(), 0)


class QueryStatsMiddlewareTestCase(SimpleTestCase):
    """Test cases for QueryStatsMiddleware."""

    def setUp(self) -> None:
        _query_count.set(0)
        _query_duration_ns.set(0)
        structlog.contextvars.clear_contextvars()

    def tearDown(self) -> None:
        _query_count.set(0)
        _query_duration_ns.set(0)
        structlog.contextvars.clear_contextvars()

    def _get_response(self, request: HttpRequest) -> HttpResponse:
        return HttpResponse("OK")

    def test_binds_stats_to_contextvars(self) -> None:
        """Test that middleware binds db_query_count and db_query_duration_ms."""
        middleware = QueryStatsMiddleware(self._get_response)
        request = HttpRequest()

        with patch.object(
            structlog.contextvars,
            "bind_contextvars",
            wraps=structlog.contextvars.bind_contextvars,
        ) as mock_bind:
            middleware(request)
            mock_bind.assert_called_once_with(
                db_query_count=0,
                db_query_duration_ms=0.0,
            )

    def test_resets_stats_per_request(self) -> None:
        """Test that stats are reset at the start of each request."""
        _query_count.set(99)
        _query_duration_ns.set(999_999_999)

        middleware = QueryStatsMiddleware(self._get_response)
        request = HttpRequest()

        with patch.object(
            structlog.contextvars,
            "bind_contextvars",
            wraps=structlog.contextvars.bind_contextvars,
        ) as mock_bind:
            middleware(request)
            mock_bind.assert_called_once_with(
                db_query_count=0,
                db_query_duration_ms=0.0,
            )

    def test_returns_response(self) -> None:
        """Test that the response from get_response is returned."""
        middleware = QueryStatsMiddleware(self._get_response)
        request = HttpRequest()

        response = middleware(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"OK")


class QueryStatsIntegrationTestCase(TransactionTestCase):
    """Integration tests that execute real DB queries."""

    def setUp(self) -> None:
        _query_count.set(0)
        _query_duration_ns.set(0)
        structlog.contextvars.clear_contextvars()

    def tearDown(self) -> None:
        _query_count.set(0)
        _query_duration_ns.set(0)
        structlog.contextvars.clear_contextvars()

    def test_counts_real_queries(self) -> None:
        """Test that real DB queries are counted by the middleware."""

        def view(request: HttpRequest) -> HttpResponse:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.execute("SELECT 2")
                cursor.execute("SELECT 3")
            return HttpResponse("OK")

        middleware = QueryStatsMiddleware(view)
        request = HttpRequest()

        with patch.object(
            structlog.contextvars,
            "bind_contextvars",
            wraps=structlog.contextvars.bind_contextvars,
        ) as mock_bind:
            middleware(request)
            mock_bind.assert_called_once()
            kwargs = mock_bind.call_args[1]
            self.assertEqual(kwargs["db_query_count"], 3)
            self.assertGreater(kwargs["db_query_duration_ms"], 0)

    def test_multiple_queries_accumulate(self) -> None:
        """Test that multiple queries accumulate correctly."""

        def view(request: HttpRequest) -> HttpResponse:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            with connection.cursor() as cursor:
                cursor.execute("SELECT 2")
            return HttpResponse("OK")

        middleware = QueryStatsMiddleware(view)
        request = HttpRequest()

        with patch.object(
            structlog.contextvars,
            "bind_contextvars",
            wraps=structlog.contextvars.bind_contextvars,
        ) as mock_bind:
            middleware(request)
            kwargs = mock_bind.call_args[1]
            self.assertEqual(kwargs["db_query_count"], 2)
