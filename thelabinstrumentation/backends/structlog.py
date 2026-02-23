from __future__ import annotations

from typing import Any

from django.utils import timezone
import structlog

from .base import MetricData, MetricsBackend

logger = structlog.get_logger(__name__)


class StructlogBackend(MetricsBackend):
    """Structlog metrics backend implementation."""

    def __init__(self, **kwargs: Any) -> None:
        pass

    def send_metrics(self, metrics: list[MetricData]) -> None:
        for metric in metrics:
            event_kwargs: dict[str, Any] = {
                "name": metric["name"],
                "value": metric["value"],
                "dimensions": self._get_all_dimensions(metric.get("dimensions")),
                "timestamp": (metric.get("timestamp") or timezone.now()).isoformat(),
            }
            unit = metric.get("unit")
            if unit is not None:
                event_kwargs["unit"] = unit
            logger.info("send_metric", **event_kwargs)
