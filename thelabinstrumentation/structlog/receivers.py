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
    if user and hasattr(user, "username") and user.is_authenticated:
        structlog.contextvars.bind_contextvars(username=user.username)


def _get_task_metadata(task_result: TaskResult[Any], **extra: Any) -> dict[str, Any]:
    """Build common task metadata to structlog contextvars.

    The django-tasks library guarantees that task_result.id, task_result.task,
    and task_result.task.module_path are always valid when signals fire. If the
    task function can't be resolved (e.g. module deleted), the signal is not
    dispatched at all.

    Returns the bound metadata dict for use with bind_contextvars() or
    bound_contextvars().
    """
    metadata: dict[str, Any] = {
        "task_id": str(task_result.id),
        "task_path": task_result.task.module_path,
        **extra,
    }
    return metadata


def _on_task_enqueued(
    sender: type[BaseTaskBackend] | None, task_result: TaskResult[Any], **kwargs: Any
) -> None:
    """Log task enqueue event with task metadata.

    Uses bound_contextvars so task_id/task_path don't persist in the request
    context after the log call (a request may enqueue multiple tasks).
    """
    metadata = _get_task_metadata(task_result)
    with structlog.contextvars.bound_contextvars(**metadata):
        logger.info("Task enqueued")


def _on_task_started(
    sender: type[BaseTaskBackend] | None, task_result: TaskResult[Any], **kwargs: Any
) -> None:
    """Clear contextvars and bind task metadata on task start."""
    structlog.contextvars.clear_contextvars()
    # Use `bind_contextvars` here instead of the `bound_contextvars` context
    # manager so that tast_id and things persist through to log lines from the
    # task execution itself. These are then cleared by `_on_task_finished`.
    structlog.contextvars.bind_contextvars(**_get_task_metadata(task_result))
    logger.info("Task started")


def _on_task_finished(
    sender: type[BaseTaskBackend] | None, task_result: TaskResult[Any], **kwargs: Any
) -> None:
    """Log task completion and clear contextvars."""
    structlog.contextvars.bind_contextvars(
        **_get_task_metadata(
            task_result,
            task_status=str(task_result.status),
        )
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
