from datetime import datetime
from unittest import TestCase
from unittest.mock import Mock, patch

import structlog.testing

from ...backends.structlog import StructlogBackend


class StructlogBackendTestCase(TestCase):
    """Test cases for the structlog metrics backend."""

    def setUp(self) -> None:
        self.backend = StructlogBackend()

    @patch("thelabinstrumentation.backends.structlog.logger")
    def test_send_metric_basic(self, mock_logger: Mock) -> None:
        """Test sending a basic metric with only name and value."""
        current_time = datetime(2023, 1, 1, 12, 0, 0)

        with (
            patch.object(
                self.backend, "_get_all_dimensions", return_value={}
            ) as mock_dims,
            patch("django.utils.timezone.now", return_value=current_time),
        ):
            self.backend.send_metric({"name": "test_metric", "value": 42.0})

            mock_dims.assert_called_once_with(None)

            mock_logger.info.assert_called_once_with(
                "send_metric",
                name="test_metric",
                value=42.0,
                dimensions={},
                timestamp=current_time.isoformat(),
            )

    @patch("thelabinstrumentation.backends.structlog.logger")
    def test_send_metric_with_unit(self, mock_logger: Mock) -> None:
        """Test sending a metric with a unit."""
        current_time = datetime(2023, 1, 1, 12, 0, 0)
        with (
            patch.object(self.backend, "_get_all_dimensions", return_value={}),
            patch("django.utils.timezone.now", return_value=current_time),
        ):
            self.backend.send_metric(
                {"name": "test_metric", "value": 42.0, "unit": "Count"}
            )

        mock_logger.info.assert_called_once_with(
            "send_metric",
            name="test_metric",
            value=42.0,
            dimensions={},
            timestamp=current_time.isoformat(),
            unit="Count",
        )

    @patch("thelabinstrumentation.backends.structlog.logger")
    def test_send_metric_with_dimensions(self, mock_logger: Mock) -> None:
        """Test sending a metric with dimensions."""
        all_dimensions = {"service": "api", "env": "test"}
        current_time = datetime(2023, 1, 1, 12, 0, 0)

        with (
            patch.object(
                self.backend,
                "_get_all_dimensions",
                return_value=all_dimensions,
            ) as mock_dims,
            patch("django.utils.timezone.now", return_value=current_time),
        ):
            self.backend.send_metric(
                {"name": "test_metric", "value": 42.0, "dimensions": {"service": "api"}}
            )

            mock_dims.assert_called_once_with({"service": "api"})

            mock_logger.info.assert_called_once_with(
                "send_metric",
                name="test_metric",
                value=42.0,
                dimensions=all_dimensions,
                timestamp=current_time.isoformat(),
            )

    @patch("thelabinstrumentation.backends.structlog.logger")
    def test_send_metric_with_timestamp(self, mock_logger: Mock) -> None:
        """Test sending a metric with an explicit timestamp."""
        timestamp = datetime(2023, 1, 1, 12, 0, 0)

        with patch.object(self.backend, "_get_all_dimensions", return_value={}):
            self.backend.send_metric(
                {"name": "test_metric", "value": 42.0, "timestamp": timestamp}
            )

        mock_logger.info.assert_called_once_with(
            "send_metric",
            name="test_metric",
            value=42.0,
            dimensions={},
            timestamp=timestamp.isoformat(),
        )

    @patch("thelabinstrumentation.backends.structlog.logger")
    def test_send_metric_with_all_parameters(self, mock_logger: Mock) -> None:
        """Test sending a metric with all parameters."""
        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        all_dimensions = {"service": "api", "env": "test"}

        with patch.object(
            self.backend,
            "_get_all_dimensions",
            return_value=all_dimensions,
        ):
            self.backend.send_metric(
                {
                    "name": "test_metric",
                    "value": 42.0,
                    "unit": "Count",
                    "dimensions": {"service": "api"},
                    "timestamp": timestamp,
                }
            )

            mock_logger.info.assert_called_once_with(
                "send_metric",
                name="test_metric",
                value=42.0,
                dimensions=all_dimensions,
                timestamp=timestamp.isoformat(),
                unit="Count",
            )

    @patch("thelabinstrumentation.backends.structlog.logger")
    def test_send_metrics_batch(self, mock_logger: Mock) -> None:
        """Test sending a batch of metrics."""
        current_time = datetime(2023, 1, 1, 12, 0, 0)

        with (
            patch.object(self.backend, "_get_all_dimensions", return_value={}),
            patch("django.utils.timezone.now", return_value=current_time),
        ):
            self.backend.send_metrics(
                [
                    {"name": "metric_1", "value": 1.0},
                    {"name": "metric_2", "value": 2.0},
                ]
            )

        self.assertEqual(mock_logger.info.call_count, 2)
        mock_logger.info.assert_any_call(
            "send_metric",
            name="metric_1",
            value=1.0,
            dimensions={},
            timestamp=current_time.isoformat(),
        )
        mock_logger.info.assert_any_call(
            "send_metric",
            name="metric_2",
            value=2.0,
            dimensions={},
            timestamp=current_time.isoformat(),
        )

    def test_send_metric_with_real_logger(self) -> None:
        """Test integration with a real structlog logger using capture_logs."""
        current_time = datetime(2023, 1, 1, 12, 0, 0)

        with (
            structlog.testing.capture_logs() as captured,
            patch.object(self.backend, "_get_all_dimensions", return_value={}),
            patch("django.utils.timezone.now", return_value=current_time),
        ):
            self.backend.send_metric(
                {"name": "real_log_test", "value": 123.45, "unit": "Count"}
            )

        self.assertEqual(len(captured), 1)
        log_entry = captured[0]
        self.assertEqual(log_entry["event"], "send_metric")
        self.assertEqual(log_entry["log_level"], "info")
        self.assertEqual(log_entry["name"], "real_log_test")
        self.assertEqual(log_entry["value"], 123.45)
        self.assertEqual(log_entry["unit"], "Count")
        self.assertEqual(log_entry["dimensions"], {})
        self.assertEqual(log_entry["timestamp"], current_time.isoformat())
