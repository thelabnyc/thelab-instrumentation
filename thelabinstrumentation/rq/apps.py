from django.apps import AppConfig


class ThelabInstrumentationRqConfig(AppConfig):
    name = "thelabinstrumentation.rq"
    label = "thelabinstrumentation_rq"

    def ready(self) -> None:
        """Initialize RQ monitoring when Django starts."""
        from .daemon import ensure_bg_sender_thread_running

        ensure_bg_sender_thread_running()
