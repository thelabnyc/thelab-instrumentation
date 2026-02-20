from django.test import SimpleTestCase, override_settings

from ...conf import InstrumentationConfig


class StructlogRequestHeadersConfigTestCase(SimpleTestCase):
    """Test cases for the structlog_request_headers config property."""

    def test_default_value(self) -> None:
        """Test default structlog_request_headers when not configured."""
        with override_settings(THELAB_INSTRUMENTATION={}):
            cfg = InstrumentationConfig()
            self.assertEqual(
                cfg.structlog_request_headers,
                {
                    "x-amz-cf-id": "cf_id",
                    "x-amzn-trace-id": "x_amzn_trace_id",
                },
            )

    def test_custom_value(self) -> None:
        """Test custom structlog_request_headers from settings."""
        custom_headers = {
            "x-custom-header": "custom_header",
            "x-request-id": "request_id",
        }
        with override_settings(
            THELAB_INSTRUMENTATION={"STRUCTLOG_REQUEST_HEADERS": custom_headers}
        ):
            cfg = InstrumentationConfig()
            self.assertEqual(cfg.structlog_request_headers, custom_headers)
