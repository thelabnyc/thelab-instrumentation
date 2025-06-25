from datetime import datetime
from typing import TYPE_CHECKING
import json
import logging

from django.utils import timezone

from .base import MetricsBackend

if TYPE_CHECKING:
    from mypy_boto3_cloudwatch.literals import StandardUnitType
else:
    StandardUnitType = str

logger = logging.getLogger(__name__)


class LoggingBackend(MetricsBackend):
    """Logging metrics backend implementation."""

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
