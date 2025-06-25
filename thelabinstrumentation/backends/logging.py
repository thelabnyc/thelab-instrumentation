from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
import json
import logging

from django.utils import timezone

from .base import MetricsBackend

if TYPE_CHECKING:
    from mypy_boto3_cloudwatch.literals import StandardUnitType

logger = logging.getLogger(__name__)


class LoggingBackend(MetricsBackend):
    """Logging metrics backend implementation."""

    def __init__(self, **kwargs: Any) -> None:
        pass

    def send_metric(
        self,
        metric_name: str,
        value: float,
        unit: StandardUnitType | None = None,
        dimensions: dict[str, str] | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        """Log a single metric."""
        metric_data = {
            "name": metric_name,
            "value": value,
            "unit": unit,
            "dimensions": self._get_all_dimensions(dimensions),
            "timestamp": (timestamp or timezone.now()).isoformat(),
        }
        logger.info("SENDMETRIC: %s", json.dumps(metric_data))
