from datetime import datetime
from typing import TYPE_CHECKING
from unittest import TestCase

from django.test import override_settings

from ...backends.base import MetricData, MetricsBackend

if TYPE_CHECKING:
    from mypy_boto3_cloudwatch.literals import StandardUnitType
else:
    StandardUnitType = str


class ConcreteBackend(MetricsBackend):
    """Concrete implementation of MetricsBackend for testing."""

    def __init__(self) -> None:
        self.last_metric: dict[str, object] | None = None

    def send_metric(
        self,
        metric_name: str,
        value: float,
        unit: StandardUnitType | None = None,
        dimensions: dict[str, str] | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        """Record the metric for testing."""
        self.last_metric = {
            "metric_name": metric_name,
            "value": value,
            "unit": unit,
            "dimensions": dimensions,
            "timestamp": timestamp,
        }


class BaseBackendTestCase(TestCase):
    """Test cases for the base metrics backend."""

    def test_cannot_instantiate_abstract_class(self) -> None:
        """Test that MetricsBackend cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            MetricsBackend()  # type: ignore

    def test_concrete_implementation(self) -> None:
        """Test that a concrete implementation can be instantiated."""
        backend = ConcreteBackend()
        self.assertIsInstance(backend, MetricsBackend)

        # Test sending a metric
        backend.send_metric("test_metric", 42.0)
        assert backend.last_metric is not None
        self.assertEqual(backend.last_metric["metric_name"], "test_metric")
        self.assertEqual(backend.last_metric["value"], 42.0)

    @override_settings(
        THELAB_INSTRUMENTATION={"DIMENSIONS": {"env": "test", "service": "backend"}}
    )
    def test_get_all_dimensions(self) -> None:
        """Test the _get_all_dimensions method."""
        backend = ConcreteBackend()

        # Test with no additional dimensions
        all_dims = backend._get_all_dimensions()
        self.assertEqual(all_dims, {"env": "test", "service": "backend"})

        # Test with additional dimensions
        all_dims = backend._get_all_dimensions({"instance": "worker-1"})
        self.assertEqual(
            all_dims, {"env": "test", "service": "backend", "instance": "worker-1"}
        )

        # Test that original dimensions are not overridden
        all_dims = backend._get_all_dimensions({"env": "prod"})
        self.assertEqual(all_dims, {"env": "prod", "service": "backend"})

    def test_metric_data_type(self) -> None:
        """Test the MetricData TypedDict."""
        # Create valid MetricData instances with various combinations
        data: MetricData = {"value": 42.0}
        self.assertEqual(data["value"], 42.0)

        data = {"value": 42.0, "unit": "Count"}
        self.assertEqual(data["unit"], "Count")

        data = {"value": 42.0, "dimensions": {"service": "api"}}
        self.assertEqual(data["dimensions"], {"service": "api"})

        now = datetime.now()
        data = {"value": 42.0, "timestamp": now}
        self.assertEqual(data["timestamp"], now)

        # Full data
        data = {
            "value": 42.0,
            "unit": "Count",
            "dimensions": {"service": "api"},
            "timestamp": now,
        }
        self.assertEqual(data["value"], 42.0)
        self.assertEqual(data["unit"], "Count")
        self.assertEqual(data["dimensions"], {"service": "api"})
        self.assertEqual(data["timestamp"], now)
