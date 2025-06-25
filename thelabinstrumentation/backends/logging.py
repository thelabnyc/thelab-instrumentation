from __future__ import annotations

from typing import Any
import json
import logging

from django.utils import timezone

from .base import MetricData, MetricsBackend

logger = logging.getLogger(__name__)


class LoggingBackend(MetricsBackend):
    """Logging metrics backend implementation."""

    def __init__(self, **kwargs: Any) -> None:
        pass

    def send_metrics(
        self,
        metrics: list[MetricData],
    ) -> None:
        """Log a single metric."""
        for metric in metrics:
            _metric = metric | {
                "dimensions": self._get_all_dimensions(metric.get("dimensions")),
                "timestamp": (metric.get("timestamp") or timezone.now()).isoformat(),
            }
            logger.info("SENDMETRIC: %s", json.dumps(_metric))
