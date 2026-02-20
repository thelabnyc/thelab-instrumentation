from django.apps import AppConfig


class ThelabInstrumentationStructlogConfig(AppConfig):
    name = "thelabinstrumentation.structlog"
    label = "thelabinstrumentation_structlog"

    def ready(self) -> None:
        from . import receivers  # noqa: F401 - connects @receiver handlers

        receivers.connect_task_signals()
