from unittest.mock import Mock, patch

from django.test import SimpleTestCase
import structlog.contextvars

from ...structlog.receivers import (
    _on_task_enqueued,
    _on_task_finished,
    _on_task_started,
    bind_username,
)


class BindUsernameTestCase(SimpleTestCase):
    """Test cases for the bind_username signal receiver."""

    def setUp(self) -> None:
        structlog.contextvars.clear_contextvars()

    def tearDown(self) -> None:
        structlog.contextvars.clear_contextvars()

    def test_binds_username(self) -> None:
        """Test that username is bound when user has a username."""
        request = Mock()
        request.user = Mock()
        request.user.username = "testuser"

        bind_username(sender=object, request=request)

        ctx = structlog.contextvars.get_contextvars()
        self.assertEqual(ctx["username"], "testuser")

    def test_binds_empty_string_when_username_is_none(self) -> None:
        """Test that empty string is bound when username is None."""
        request = Mock()
        request.user = Mock()
        request.user.username = None

        bind_username(sender=object, request=request)

        ctx = structlog.contextvars.get_contextvars()
        self.assertEqual(ctx["username"], "")

    def test_no_bind_when_no_user(self) -> None:
        """Test that nothing is bound when request has no user attribute."""
        request = Mock(spec=[])  # No attributes at all

        bind_username(sender=object, request=request)

        ctx = structlog.contextvars.get_contextvars()
        self.assertNotIn("username", ctx)


def _make_task_result(
    task_id: str = "task-123",
    module_path: str = "myapp.tasks.do_work",
    status: str = "SUCCESSFUL",
) -> Mock:
    """Create a mock TaskResult with nested task.module_path."""
    task_result = Mock()
    task_result.id = task_id
    task_result.task.module_path = module_path
    task_result.status = status
    return task_result


class TaskEnqueuedTestCase(SimpleTestCase):
    """Test cases for _on_task_enqueued."""

    def setUp(self) -> None:
        structlog.contextvars.clear_contextvars()

    def tearDown(self) -> None:
        structlog.contextvars.clear_contextvars()

    def test_binds_task_metadata(self) -> None:
        """Test that task_id and task_path are bound on enqueue."""
        task_result = _make_task_result(task_id="task-123")

        with patch("thelabinstrumentation.structlog.receivers.logger") as mock_logger:
            _on_task_enqueued(sender=None, task_result=task_result)

        ctx = structlog.contextvars.get_contextvars()
        self.assertEqual(ctx["task_id"], "task-123")
        self.assertEqual(ctx["task_path"], "myapp.tasks.do_work")
        mock_logger.info.assert_called_once_with("Task enqueued")


class TaskStartedTestCase(SimpleTestCase):
    """Test cases for _on_task_started."""

    def setUp(self) -> None:
        structlog.contextvars.clear_contextvars()

    def tearDown(self) -> None:
        structlog.contextvars.clear_contextvars()

    def test_clears_and_binds_task_metadata(self) -> None:
        """Test that contextvars are cleared and task metadata is bound."""
        # Pre-populate some contextvars
        structlog.contextvars.bind_contextvars(stale_key="should_be_cleared")

        task_result = _make_task_result(task_id="task-456")

        with patch("thelabinstrumentation.structlog.receivers.logger") as mock_logger:
            _on_task_started(sender=None, task_result=task_result)

        ctx = structlog.contextvars.get_contextvars()
        self.assertNotIn("stale_key", ctx)
        self.assertEqual(ctx["task_id"], "task-456")
        self.assertEqual(ctx["task_path"], "myapp.tasks.do_work")
        mock_logger.info.assert_called_once_with("Task started")


class TaskFinishedTestCase(SimpleTestCase):
    """Test cases for _on_task_finished."""

    def setUp(self) -> None:
        structlog.contextvars.clear_contextvars()

    def tearDown(self) -> None:
        structlog.contextvars.clear_contextvars()

    def test_logs_success_and_clears(self) -> None:
        """Test that success is logged and contextvars are cleared."""
        task_result = _make_task_result(task_id="task-789", status="SUCCESSFUL")

        with patch("thelabinstrumentation.structlog.receivers.logger") as mock_logger:
            _on_task_finished(sender=None, task_result=task_result)

        mock_logger.info.assert_called_once_with("Task finished")
        mock_logger.warning.assert_not_called()
        ctx = structlog.contextvars.get_contextvars()
        self.assertEqual(ctx, {})

    def test_logs_failure(self) -> None:
        """Test that failure status triggers a warning log."""
        task_result = _make_task_result(task_id="task-999", status="FAILED")

        with patch("thelabinstrumentation.structlog.receivers.logger") as mock_logger:
            _on_task_finished(sender=None, task_result=task_result)

        mock_logger.warning.assert_called_once_with("Task finished with failure")
        mock_logger.info.assert_not_called()
        ctx = structlog.contextvars.get_contextvars()
        self.assertEqual(ctx, {})


class ConnectTaskSignalsTestCase(SimpleTestCase):
    """Test cases for connect_task_signals."""

    def test_noop_when_no_tasks_package(self) -> None:
        """Test that connect_task_signals is a no-op when neither package is available."""
        with (
            patch.dict(
                "sys.modules",
                {
                    "django.tasks": None,
                    "django.tasks.signals": None,
                    "django_tasks": None,
                    "django_tasks.signals": None,
                },
            ),
        ):
            from ...structlog.receivers import connect_task_signals

            connect_task_signals()

    def test_connects_signals_when_available(self) -> None:
        """Test that task signals are connected when django_tasks is available."""
        mock_enqueued = Mock()
        mock_started = Mock()
        mock_finished = Mock()

        signals_module = Mock()
        signals_module.task_enqueued = mock_enqueued
        signals_module.task_started = mock_started
        signals_module.task_finished = mock_finished

        with patch.dict(
            "sys.modules",
            {
                "django.tasks": None,
                "django.tasks.signals": None,
                "django_tasks.signals": signals_module,
            },
        ):
            from ...structlog.receivers import connect_task_signals

            connect_task_signals()

        mock_enqueued.connect.assert_called_once()
        mock_started.connect.assert_called_once()
        mock_finished.connect.assert_called_once()
