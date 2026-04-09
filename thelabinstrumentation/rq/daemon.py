from threading import local
import logging
import threading
import time

from redis.exceptions import ConnectionError as RedisConnectionError
from rq import Worker
import django_rq
import sentry_sdk

from ..backends import MetricData, MetricsBackend, get_backend
from ..conf import config

logger = logging.getLogger(__name__)

_threadlocals = local()

# Max backoff multiplier when Redis is unavailable (caps at ~5 minutes with default 60s interval)
_MAX_BACKOFF_MULTIPLIER = 5


class BackgroundMetricsSenderThread(threading.Thread):
    def run(self) -> None:
        backend = get_backend()
        consecutive_conn_failures = 0
        while True:
            try:
                self.send_metrics(backend)
                consecutive_conn_failures = 0
            except (RedisConnectionError, ConnectionError):
                consecutive_conn_failures += 1
                if consecutive_conn_failures == 1:
                    logger.debug("Redis unavailable, skipping RQ metrics")
                elif consecutive_conn_failures % 10 == 0:
                    logger.debug(
                        "Redis still unavailable, skipping RQ metrics (attempt %d)",
                        consecutive_conn_failures,
                    )
            except Exception:
                consecutive_conn_failures = 0
                logger.exception("Error sending RQ metrics")
                sentry_sdk.capture_exception()
            backoff = min(consecutive_conn_failures, _MAX_BACKOFF_MULTIPLIER)
            time.sleep(config.update_interval * max(1, backoff))

    def send_metrics(self, backend: MetricsBackend) -> None:
        queues = django_rq.queues.get_queues()  # type:ignore[no-untyped-call]
        batch: list[MetricData] = []
        for queue in queues:
            dimensions = {
                "QueueName": queue.name,
            }
            queued_jobs = queue.count
            num_workers = Worker.count(queue=queue)
            finished_jobs = queue.finished_job_registry.get_job_count(
                cleanup=False,
            )
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
                    "value": finished_jobs,
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
