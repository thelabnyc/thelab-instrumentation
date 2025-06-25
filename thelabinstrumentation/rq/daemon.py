from threading import local
import logging
import threading
import time

from django_rq.utils import get_statistics
import sentry_sdk

from ..backends.base import MetricsBackend
from ..backends.factory import get_backend
from ..conf import config

logger = logging.getLogger(__name__)

_threadlocals = local()


class BackgroundMetricsSenderThread(threading.Thread):
    def run(self) -> None:
        backend = get_backend()
        while True:
            try:
                self.send_metrics(backend)
            except Exception:
                logger.exception("Error sending RQ metrics")
                sentry_sdk.capture_exception()
            time.sleep(config.update_interval)

    def send_metrics(self, backend: MetricsBackend) -> None:
        stats = get_statistics()  # type:ignore[no-untyped-call]
        for queue_stats in stats["queues"]:
            for our_name, stat_name in [
                ("rq.queued-jobs", "jobs"),
                # ("rq.finished-jobs", "finished_jobs"),
                # ("rq.started-jobs", "started_jobs"),
                # ("rq.failed-jobs", "failed_jobs"),
            ]:
                backend.send_metric(
                    our_name,
                    value=queue_stats[stat_name],
                    unit="Count",
                    dimensions={
                        "QueueName": queue_stats["name"],
                    },
                )


def ensure_bg_sender_thread_running() -> BackgroundMetricsSenderThread:
    if (
        not hasattr(_threadlocals, "bg_thread")
        or not _threadlocals.bg_thread.is_alive()
    ):
        _threadlocals.bg_thread = BackgroundMetricsSenderThread(daemon=True)
        _threadlocals.bg_thread.start()
    return _threadlocals.bg_thread  # type:ignore[no-any-return]
