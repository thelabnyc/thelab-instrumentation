from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, TypedDict

from ..conf import config

if TYPE_CHECKING:
    from mypy_boto3_cloudwatch.literals import StandardUnitType
else:
    StandardUnitType = str


class MetricData(TypedDict, total=False):
    """Type definition for metric data."""

    value: float
    unit: StandardUnitType | None
    dimensions: dict[str, str] | None
    timestamp: datetime | None


class MetricsBackend(ABC):
    """Abstract base class for metrics backends."""

    @abstractmethod
    def send_metric(
        self,
        metric_name: str,
        value: float,
        unit: StandardUnitType | None = None,
        dimensions: dict[str, str] | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        """Send a single metric."""
        pass

    def _get_all_dimensions(
        self, dimensions: dict[str, str] | None = None
    ) -> dict[str, str]:
        return config.dimensions | (dimensions or {})
