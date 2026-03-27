from typing import Any, TypedDict, cast

from django.conf import settings


class InstrumentationConfigData(TypedDict, total=False):
    BACKEND: str
    OPTIONS: dict[str, Any]
    DIMENSIONS: dict[str, str]
    UPDATE_INTERVAL: int
    STRUCTLOG_REQUEST_HEADERS: dict[str, str]
    OUTGOING_HTTP_EXCLUDE_HOSTS: list[str]


class InstrumentationConfig:
    """Configuration manager for TheLab Instrumentation settings."""

    @property
    def config(self) -> InstrumentationConfigData:
        config = getattr(settings, "THELAB_INSTRUMENTATION", {})
        return cast(InstrumentationConfigData, config)

    @property
    def backend(self) -> str:
        """Backend class path to use for metrics."""
        return self.config.get(
            "BACKEND", "thelabinstrumentation.backends.logging.LoggingBackend"
        )

    @property
    def backend_options(self) -> dict[str, Any]:
        """Options to pass to the backend constructor as kwargs."""
        return self.config.get("OPTIONS") or {}

    @property
    def dimensions(self) -> dict[str, str]:
        """Dimensions to include with every metric"""
        return self.config.get("DIMENSIONS", {})

    @property
    def update_interval(self) -> int:
        """Interval in seconds between metric updates."""
        return self.config.get("UPDATE_INTERVAL", 60)

    @property
    def outgoing_http_exclude_hosts(self) -> set[str]:
        """Set of hostnames to exclude from outgoing HTTP logging."""
        return set(self.config.get("OUTGOING_HTTP_EXCLUDE_HOSTS", []))

    @property
    def structlog_request_headers(self) -> dict[str, str]:
        """Header name -> structlog context var name mapping."""
        return self.config.get(
            "STRUCTLOG_REQUEST_HEADERS",
            {
                "x-amz-cf-id": "cf_id",
                "x-amzn-trace-id": "x_amzn_trace_id",
            },
        )


# Global configuration instance
config = InstrumentationConfig()
