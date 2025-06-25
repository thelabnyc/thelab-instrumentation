from django.utils.module_loading import import_string

from ..conf import config
from .base import MetricsBackend


def get_backend() -> MetricsBackend:
    """
    Get the metrics backend instance based on configuration.
    """
    backend_class: type[MetricsBackend] = import_string(config.backend)
    assert issubclass(backend_class, MetricsBackend)
    return backend_class(**config.backend_options)
