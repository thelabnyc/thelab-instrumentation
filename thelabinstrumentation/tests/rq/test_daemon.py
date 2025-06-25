from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, Mock, patch

from django.test import SimpleTestCase

from ...backends.base import MetricsBackend
from ...rq.daemon import (
    BackgroundMetricsSenderThread,
    _threadlocals,
    ensure_bg_sender_thread_running,
)


class ConcreteMetricsBackend(MetricsBackend):
    """Concrete implementation of MetricsBackend for testing."""

    def __init__(self) -> None:
        self.metrics: list[dict[str, Any]] = []

    def send_metric(
        self,
        metric_name: str,
        value: float,
        unit: str | None = None,
        dimensions: dict[str, str] | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        """Record the metric for testing."""
        self.metrics.append(
            {
                "metric_name": metric_name,
                "value": value,
                "unit": unit,
                "dimensions": dimensions,
                "timestamp": timestamp,
            }
        )


class BackgroundMetricsSenderThreadTestCase(SimpleTestCase):
    """Test cases for the BackgroundMetricsSenderThread class."""

    @patch("thelabinstrumentation.rq.daemon.get_statistics")
    def test_send_metrics(self, mock_get_statistics: Mock) -> None:
        """Test the send_metrics method."""
        # Setup test data to avoid actual Redis connection
        mock_get_statistics.return_value = {
            "queues": [
                {
                    "name": "default",
                    "jobs": 10,
                    "finished_jobs": 20,
                    "started_jobs": 30,
                    "failed_jobs": 5,
                },
                {
                    "name": "high",
                    "jobs": 5,
                    "finished_jobs": 15,
                    "started_jobs": 25,
                    "failed_jobs": 2,
                },
            ]
        }

        # Create a concrete backend to test with
        backend = ConcreteMetricsBackend()

        # Create thread and call send_metrics
        thread = BackgroundMetricsSenderThread()
        thread.send_metrics(backend)

        # We should have 2 metrics: 1 for each of the 2 queues
        self.assertEqual(len(backend.metrics), 2)

        # Check metrics for the default queue
        default_metrics = [
            m for m in backend.metrics if m["dimensions"]["QueueName"] == "default"
        ]
        self.assertEqual(len(default_metrics), 1)

        # Verify each metric for default queue
        self.assertEqual(
            [m for m in default_metrics if m["metric_name"] == "rq.queued-jobs"][0][
                "value"
            ],
            10,
        )

        # Check metrics for the high queue
        high_metrics = [
            m for m in backend.metrics if m["dimensions"]["QueueName"] == "high"
        ]
        self.assertEqual(len(high_metrics), 1)

        # Verify each metric for high queue
        self.assertEqual(
            [m for m in high_metrics if m["metric_name"] == "rq.queued-jobs"][0][
                "value"
            ],
            5,
        )

    @patch("thelabinstrumentation.rq.daemon.time.sleep")
    @patch("thelabinstrumentation.rq.daemon.sentry_sdk")
    @patch("thelabinstrumentation.rq.daemon.get_backend")
    def test_run_method(
        self, mock_get_backend: Mock, mock_sentry_sdk: Mock, mock_sleep: Mock
    ) -> None:
        """Test the run method."""
        # Setup mocks
        mock_backend = Mock()
        mock_get_backend.return_value = mock_backend

        # Make sleep raise exception after first call to break the infinite loop
        mock_sleep.side_effect = [Exception("Stop loop")]

        # Create thread and patch send_metrics to avoid actual sending
        thread = BackgroundMetricsSenderThread()
        thread.send_metrics = MagicMock()  # type: ignore

        # Run the thread method and catch the exception we use to break the loop
        with self.assertRaises(Exception) as context:
            thread.run()

        self.assertEqual(str(context.exception), "Stop loop")

        # Verify send_metrics was called with the backend
        thread.send_metrics.assert_called_with(mock_backend)
        self.assertEqual(thread.send_metrics.call_count, 1)

        # Verify sleep was called
        mock_sleep.assert_called_once()

        # Test exception handling
        thread.send_metrics.reset_mock()
        mock_sleep.reset_mock()

        # Make send_metrics raise an exception, then sleep raise exception
        thread.send_metrics.side_effect = Exception("Metric error")
        mock_sleep.side_effect = Exception("Stop loop")

        # Run again and it should handle the exception from send_metrics
        with self.assertRaises(Exception) as context:
            thread.run()

        self.assertEqual(str(context.exception), "Stop loop")

        # Verify the exception was captured by Sentry
        mock_sentry_sdk.capture_exception.assert_called_once()

        # Verify sleep was called
        mock_sleep.assert_called_once()


class EnsureBgSenderThreadRunningTestCase(SimpleTestCase):
    """Test cases for the ensure_bg_sender_thread_running function."""

    def setUp(self) -> None:
        """Set up the test case."""
        # Clear threadlocals before each test
        if hasattr(_threadlocals, "bg_thread"):
            delattr(_threadlocals, "bg_thread")

    @patch("thelabinstrumentation.rq.daemon.BackgroundMetricsSenderThread")
    def test_creates_new_thread_if_none_exists(self, mock_thread_class: Mock) -> None:
        """Test that a new thread is created if none exists."""
        # Setup mock thread
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread
        mock_thread.is_alive.return_value = True

        # Call the function
        result = ensure_bg_sender_thread_running()

        # Verify a new thread was created and started
        mock_thread_class.assert_called_once()
        self.assertTrue(mock_thread.start.called)
        self.assertEqual(result, mock_thread)

        # The thread should be stored in threadlocals
        self.assertEqual(_threadlocals.bg_thread, mock_thread)

    @patch("thelabinstrumentation.rq.daemon.BackgroundMetricsSenderThread")
    def test_returns_existing_thread_if_alive(self, mock_thread_class: Mock) -> None:
        """Test that the existing thread is returned if it's alive."""
        # Setup existing thread
        mock_existing_thread = Mock()
        mock_existing_thread.is_alive.return_value = True
        _threadlocals.bg_thread = mock_existing_thread

        # Call the function
        result = ensure_bg_sender_thread_running()

        # Verify no new thread was created
        mock_thread_class.assert_not_called()
        self.assertEqual(result, mock_existing_thread)

    @patch("thelabinstrumentation.rq.daemon.BackgroundMetricsSenderThread")
    def test_creates_new_thread_if_existing_is_dead(
        self, mock_thread_class: Mock
    ) -> None:
        """Test that a new thread is created if the existing one is dead."""
        # Setup dead existing thread
        mock_existing_thread = Mock()
        mock_existing_thread.is_alive.return_value = False
        _threadlocals.bg_thread = mock_existing_thread

        # Setup new thread
        mock_new_thread = Mock()
        mock_thread_class.return_value = mock_new_thread
        mock_new_thread.is_alive.return_value = True

        # Call the function
        result = ensure_bg_sender_thread_running()

        # Verify a new thread was created and started
        mock_thread_class.assert_called_once()
        self.assertTrue(mock_new_thread.start.called)
        self.assertEqual(result, mock_new_thread)

        # The new thread should be stored in threadlocals
        self.assertEqual(_threadlocals.bg_thread, mock_new_thread)


class AppConfigTestCase(SimpleTestCase):
    """Test integration with Django app config."""

    @patch("thelabinstrumentation.rq.daemon.ensure_bg_sender_thread_running")
    def test_ready_calls_ensure_bg_sender_thread_running(
        self, mock_ensure: Mock
    ) -> None:
        """Test that the AppConfig.ready method calls ensure_bg_sender_thread_running."""
        from thelabinstrumentation.rq.apps import ThelabInstrumentationRqConfig

        # Get the ready method directly and call it
        ready_method = ThelabInstrumentationRqConfig.ready
        # Create a mock instance
        mock_instance = Mock(spec=ThelabInstrumentationRqConfig)
        # Call the ready method with the mock instance
        ready_method(mock_instance)

        # Verify ensure_bg_sender_thread_running was called
        mock_ensure.assert_called_once()
