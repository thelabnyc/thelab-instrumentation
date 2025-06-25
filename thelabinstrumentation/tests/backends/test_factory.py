from typing import Any
from unittest import TestCase
from unittest.mock import Mock, patch

from django.test import override_settings

from ...backends.factory import get_backend
from ...backends.logging import LoggingBackend


class FactoryTestCase(TestCase):
    """Test cases for the backend factory."""

    @override_settings(
        THELAB_INSTRUMENTATION={
            "BACKEND": "thelabinstrumentation.backends.logging.LoggingBackend",
            "OPTIONS": {},
        }
    )
    def test_get_backend_with_default_options(self) -> None:
        """Test getting a backend with default options."""
        # Get the backend
        backend = get_backend()
        # Verify backend is a LoggingBackend with default options
        self.assertIsInstance(backend, LoggingBackend)

    @override_settings(
        THELAB_INSTRUMENTATION={"BACKEND": "invalid.backend.Class", "OPTIONS": {}}
    )
    @patch("thelabinstrumentation.backends.factory.import_string")
    def test_get_backend_with_invalid_class(self, mock_import_string: Mock) -> None:
        """Test getting a backend with an invalid class path."""
        # Mock import_string to raise ImportError
        mock_import_string.side_effect = ImportError(
            "Cannot import 'invalid.backend.Class'"
        )
        # Attempt to get the backend
        with self.assertRaises(ImportError):
            get_backend()

    @override_settings(
        THELAB_INSTRUMENTATION={
            "BACKEND": "thelabinstrumentation.backends.logging.LoggingBackend",
            "OPTIONS": {
                "invalid_option": "value"  # LoggingBackend doesn't accept this
            },
        }
    )
    def test_get_backend_with_invalid_options(self) -> None:
        """Test getting a backend with invalid constructor options."""
        # Attempt to get the backend - should raise TypeError for unexpected keyword
        with self.assertRaises(TypeError):
            get_backend()

    @override_settings(
        THELAB_INSTRUMENTATION={"BACKEND": "not.a.metrics.Backend", "OPTIONS": {}}
    )
    def test_get_backend_non_metrics_backend(self) -> None:
        """Test getting a backend that doesn't inherit from MetricsBackend."""

        # Create a non-MetricsBackend class
        class NotAMetricsBackend:
            def __init__(self, **kwargs: Any) -> None:
                self.kwargs = kwargs

        # Apply the mock to django's import_string function
        with patch(
            "thelabinstrumentation.backends.factory.import_string",
            return_value=NotAMetricsBackend,
        ):
            # Attempt to get the backend - should raise AssertionError
            with self.assertRaises(AssertionError):
                get_backend()
