from __future__ import annotations

from unittest import TestCase

from django.test import override_settings

from ...backends.base import MetricData, MetricsBackend


class ConcreteBackend(MetricsBackend):
    """Concrete implementation of MetricsBackend for testing."""

    metrics: list[MetricData]

    def __init__(self) -> None:
        self.metrics = []

    @property
    def last_metric(self) -> MetricData | None:
        return self.metrics[-1]

    def send_metric(
        self,
        metric: MetricData,
    ) -> None:
        """Record a single metric for testing."""
        self.metrics.append(metric)

    def send_metrics(
        self,
        metrics: list[MetricData],
    ) -> None:
        """Record the metrics for testing."""
        self.metrics += metrics


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
        backend.send_metric({"name": "test_metric", "value": 42.0})
        assert backend.last_metric is not None
        self.assertEqual(backend.last_metric["name"], "test_metric")
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
