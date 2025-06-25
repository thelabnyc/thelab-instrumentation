from typing import Any, TypedDict, cast

from django.conf import settings


class InstrumentationConfigData(TypedDict, total=False):
    BACKEND: str
    OPTIONS: dict[str, Any]
    DIMENSIONS: dict[str, str]
    UPDATE_INTERVAL: int
    RQ_QUEUES: list[str]


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
    def rq_queues(self) -> list[str]:
        """List of RQ queue names to monitor."""
        return self.config.get("RQ_QUEUES", [])


# Global configuration instance
config = InstrumentationConfig()
