from typing import cast
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from ...rq.apps import ThelabInstrumentationRqConfig


class ThelabInstrumentationRqConfigTestCase(SimpleTestCase):
    """Test cases for the ThelabInstrumentationRqConfig class."""

    def test_app_config(self) -> None:
        """Test the app configuration."""
        # Just test the class attributes directly without instantiation
        self.assertEqual(ThelabInstrumentationRqConfig.name, "thelabinstrumentation.rq")
        self.assertEqual(
            ThelabInstrumentationRqConfig.label, "thelabinstrumentation_rq"
        )

    def test_ready_method(self) -> None:
        """Test that the ready method initializes the background thread."""
        # Use a context manager for the patch to ensure proper cleanup
        with patch(
            "thelabinstrumentation.rq.daemon.ensure_bg_sender_thread_running"
        ) as mock_ensure_thread:
            # Get the ready method directly and call it
            ready_method = ThelabInstrumentationRqConfig.ready
            # Create a mock instance and call the ready method with it
            mock_instance = cast(
                ThelabInstrumentationRqConfig, Mock(spec=ThelabInstrumentationRqConfig)
            )
            ready_method(mock_instance)

            # Verify the background thread initialization was called
            mock_ensure_thread.assert_called_once()
