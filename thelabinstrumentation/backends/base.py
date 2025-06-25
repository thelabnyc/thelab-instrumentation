from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, NotRequired, TypedDict

from ..conf import config

if TYPE_CHECKING:
    from mypy_boto3_cloudwatch.literals import StandardUnitType


class MetricData(TypedDict):
    """Type definition for metric data."""

    name: str
    value: float
    unit: NotRequired[StandardUnitType]
    dimensions: NotRequired[dict[str, str]]
    timestamp: NotRequired[datetime]


class MetricsBackend(ABC):
    """Abstract base class for metrics backends."""

    def send_metric(self, metric: MetricData) -> None:
        self.send_metrics([metric])

    @abstractmethod
    def send_metrics(self, metrics: list[MetricData]) -> None:
        """Send a batch of metrics."""
        pass

    def _get_all_dimensions(
        self, dimensions: dict[str, str] | None = None
    ) -> dict[str, str]:
        return config.dimensions | (dimensions or {})
