from django.apps import AppConfig


class ThelabInstrumentationStructlogConfig(AppConfig):
    name = "thelabinstrumentation.structlog"
    label = "thelabinstrumentation_structlog"

    def ready(self) -> None:
        from . import receivers

        receivers.connect_task_signals()

        try:
            from .outgoing_http import install as install_outgoing_http_logging
        except ImportError:
            pass
        else:
            install_outgoing_http_logging()
