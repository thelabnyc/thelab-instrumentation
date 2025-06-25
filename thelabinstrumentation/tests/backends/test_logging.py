from datetime import datetime
from unittest import TestCase
from unittest.mock import Mock, patch
import json
import logging

from ...backends.logging import LoggingBackend


class LoggingBackendTestCase(TestCase):
    """Test cases for the Logging metrics backend."""

    def setUp(self) -> None:
        """Set up the test environment."""
        # Reset logging configuration to avoid interference from other tests
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        logging.basicConfig(level=logging.INFO)

        # Create the backend with default settings
        self.backend = LoggingBackend()

    @patch("logging.Logger.info")
    def test_send_metric_basic(self, mock_log: Mock) -> None:
        """Test sending a basic metric with only name and value."""
        try:
            current_time = datetime(2023, 1, 1, 12, 0, 0)

            # Mock both _get_all_dimensions and timezone.now to control test environment
            with (
                patch.object(
                    self.backend, "_get_all_dimensions", return_value={}
                ) as mock_dims,
                patch("django.utils.timezone.now", return_value=current_time),
            ):
                # Call the send_metric method with our test metric
                self.backend.send_metric({"name": "test_metric", "value": 42.0})

                # Verify the dimensions method was called with the right args
                mock_dims.assert_called_once_with(None)

                # Verify logger.info was called
                mock_log.assert_called_once()
                message, json_data = mock_log.call_args[0]
                self.assertEqual(message, "SENDMETRIC: %s")

                # Parse the JSON and verify its contents
                data = json.loads(json_data)
                print(f"DEBUG: JSON data: {data}")

                # Check all expected fields
                self.assertEqual(data["name"], "test_metric")
                self.assertEqual(data["value"], 42.0)
                self.assertEqual(data["dimensions"], {})
                self.assertEqual(data["timestamp"], current_time.isoformat())

                # Verify unit is not included (or is None)
                self.assertTrue("unit" not in data or data["unit"] is None)
        except Exception as e:
            import traceback

            print(f"ERROR in test_send_metric_basic: {type(e).__name__}: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            raise  # Re-raise the exception to fail the test

    @patch("logging.Logger.info")
    def test_send_metric_with_unit(self, mock_log: Mock) -> None:
        """Test sending a metric with a unit."""
        current_time = datetime(2023, 1, 1, 12, 0, 0)
        with (
            patch.object(self.backend, "_get_all_dimensions", return_value={}),
            patch("django.utils.timezone.now", return_value=current_time),
        ):
            self.backend.send_metric(
                {"name": "test_metric", "value": 42.0, "unit": "Count"}
            )

        # Get the JSON data from the mock call
        message, json_data = mock_log.call_args[0]
        data = json.loads(json_data)

        # Verify the unit was included in the logged data
        self.assertEqual(data["unit"], "Count")

    @patch("logging.Logger.info")
    def test_send_metric_with_dimensions(self, mock_log: Mock) -> None:
        """Test sending a metric with dimensions."""
        all_dimensions = {"service": "api", "env": "test"}

        with patch.object(
            self.backend,
            "_get_all_dimensions",
            return_value=all_dimensions,
        ):
            self.backend.send_metric(
                {"name": "test_metric", "value": 42.0, "dimensions": {"service": "api"}}
            )

            message, json_data = mock_log.call_args[0]
            data = json.loads(json_data)

            self.assertEqual(data["dimensions"], all_dimensions)

    @patch("logging.Logger.info")
    def test_send_metric_with_timestamp(self, mock_log: Mock) -> None:
        """Test sending a metric with a timestamp."""
        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        with patch.object(self.backend, "_get_all_dimensions", return_value={}):
            self.backend.send_metric(
                {"name": "test_metric", "value": 42.0, "timestamp": timestamp}
            )

        message, json_data = mock_log.call_args[0]
        data = json.loads(json_data)

        self.assertEqual(data.get("timestamp"), timestamp.isoformat())

    @patch("logging.Logger.info")
    def test_send_metric_with_all_parameters(self, mock_log: Mock) -> None:
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

            message, json_data = mock_log.call_args[0]
            data = json.loads(json_data)

            self.assertEqual(data["name"], "test_metric")
            self.assertEqual(data["value"], 42.0)
            self.assertEqual(data.get("unit"), "Count")
            self.assertEqual(data["dimensions"], all_dimensions)
            self.assertEqual(data["timestamp"], timestamp.isoformat())

    def test_log_with_actual_logger(self) -> None:
        """Test that logging actually works with a real logger."""
        current_time = datetime(2023, 1, 1, 12, 0, 0)

        # Use assertLogs to capture the log output
        with self.assertLogs(
            "thelabinstrumentation.backends.logging", level="INFO"
        ) as logs:
            # Create test environment with mocks
            with (
                patch.object(self.backend, "_get_all_dimensions", return_value={}),
                patch("django.utils.timezone.now", return_value=current_time),
            ):
                # Send a test metric
                self.backend.send_metric({"name": "real_log_test", "value": 123.45})

            # Verify log was captured
            self.assertEqual(len(logs.records), 1)
            log_message = logs.records[0].getMessage()
            self.assertTrue(log_message.startswith("SENDMETRIC: "))

            # Extract and parse the JSON part
            json_str = log_message.replace("SENDMETRIC: ", "")
            data = json.loads(json_str)

            # Verify the logged data
            self.assertEqual(data["name"], "real_log_test")
            self.assertEqual(data["value"], 123.45)
            self.assertEqual(data["timestamp"], current_time.isoformat())
            self.assertEqual(data["dimensions"], {})
            self.assertTrue("unit" not in data or data["unit"] is None)
