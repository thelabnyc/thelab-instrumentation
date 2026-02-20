from __future__ import annotations

from typing import TYPE_CHECKING, Any
import logging

from django.dispatch import receiver
from django.http import HttpRequest
from django_structlog.signals import bind_extra_request_metadata
import structlog.contextvars

if TYPE_CHECKING:
    from django_tasks.backends.base import BaseTaskBackend
    from django_tasks.base import TaskResult

logger = logging.getLogger(__name__)


@receiver(bind_extra_request_metadata)
def bind_username(sender: type[Any], request: HttpRequest, **kwargs: Any) -> None:
    """Bind the authenticated user's username to structlog context."""
    user = getattr(request, "user", None)
    if user and hasattr(user, "username"):
        structlog.contextvars.bind_contextvars(username=user.username or "")


def _on_task_enqueued(
    sender: type[BaseTaskBackend] | None, task_result: TaskResult[Any], **kwargs: Any
) -> None:
    """Log task enqueue event with task metadata."""
    structlog.contextvars.bind_contextvars(
        task_id=str(task_result.id),
        task_path=task_result.task.module_path,
    )
    logger.info("Task enqueued")


def _on_task_started(
    sender: type[BaseTaskBackend] | None, task_result: TaskResult[Any], **kwargs: Any
) -> None:
    """Clear contextvars and bind task metadata on task start."""
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        task_id=str(task_result.id),
        task_path=task_result.task.module_path,
    )
    logger.info("Task started")


def _on_task_finished(
    sender: type[BaseTaskBackend] | None, task_result: TaskResult[Any], **kwargs: Any
) -> None:
    """Log task completion and clear contextvars."""
    structlog.contextvars.bind_contextvars(
        task_id=str(task_result.id),
        task_path=task_result.task.module_path,
        task_status=str(task_result.status),
    )
    if task_result.status == "FAILED":
        logger.warning("Task finished with failure")
    else:
        logger.info("Task finished")
    structlog.contextvars.clear_contextvars()


def connect_task_signals() -> None:
    """Connect task lifecycle signal handlers.

    Tries django.tasks.signals first (Django 6+), then falls back to
    django_tasks.signals (backport). No-op if neither is available.
    """
    try:
        from django.tasks.signals import (  # type: ignore[import-untyped]
            task_enqueued,
            task_finished,
            task_started,
        )
    except ImportError:
        try:
            from django_tasks.signals import (
                task_enqueued,
                task_finished,
                task_started,
            )
        except ImportError:
            return

    task_enqueued.connect(
        _on_task_enqueued, dispatch_uid="thelabinstrumentation.on_task_enqueued"
    )
    task_started.connect(
        _on_task_started, dispatch_uid="thelabinstrumentation.on_task_started"
    )
    task_finished.connect(
        _on_task_finished, dispatch_uid="thelabinstrumentation.on_task_finished"
    )
