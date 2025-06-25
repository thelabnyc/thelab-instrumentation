from threading import local
import logging
import threading
import time

from django_rq.utils import get_statistics
import sentry_sdk

from ..backends import MetricData, MetricsBackend, get_backend
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
        batch: list[MetricData] = []
        for queue_stats in stats["queues"]:
            dimensions = {
                "QueueName": queue_stats["name"],
            }
            queued_jobs = queue_stats["jobs"]
            num_workers = queue_stats["workers"]
            queued_per_worker = (
                float(queued_jobs) / float(num_workers) if num_workers > 0 else 0
            )
            batch.append(
                {
                    "name": "rq.queued-jobs",
                    "value": queued_jobs,
                    "unit": "Count",
                    "dimensions": dimensions,
                }
            )
            batch.append(
                {
                    "name": "rq.finished-jobs",
                    "value": queue_stats["finished_jobs"],
                    "unit": "Count",
                    "dimensions": dimensions,
                }
            )
            batch.append(
                {
                    "name": "rq.workers",
                    "value": num_workers,
                    "unit": "Count",
                    "dimensions": dimensions,
                }
            )
            batch.append(
                {
                    "name": "rq.queued-jobs-per-worker",
                    "value": queued_per_worker,
                    "unit": "Count",
                    "dimensions": dimensions,
                }
            )
        backend.send_metrics(batch)


def ensure_bg_sender_thread_running() -> BackgroundMetricsSenderThread:
    if (
        not hasattr(_threadlocals, "bg_thread")
        or not _threadlocals.bg_thread.is_alive()
    ):
        _threadlocals.bg_thread = BackgroundMetricsSenderThread(daemon=True)
        _threadlocals.bg_thread.start()
    return _threadlocals.bg_thread  # type:ignore[no-any-return]
