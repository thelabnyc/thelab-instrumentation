# thelab-instrumentation

[![Latest Release](https://gitlab.com/thelabnyc/thelab-instrumentation/-/badges/release.svg)](https://gitlab.com/thelabnyc/thelab-instrumentation/-/releases)
[![pipeline status](https://gitlab.com/thelabnyc/thelab-instrumentation/badges/master/pipeline.svg)](https://gitlab.com/thelabnyc/thelab-instrumentation/-/commits/master)
[![coverage report](https://gitlab.com/thelabnyc/thelab-instrumentation/badges/master/coverage.svg)](https://gitlab.com/thelabnyc/thelab-instrumentation/-/commits/master)

A fully type-safe instrumentation and monitoring library for Django projects. This package provides:

- Metrics collection and reporting to various backends (CloudWatch, Logging)
- RQ queue monitoring
- Structured logging helpers for [django-structlog](https://django-structlog.readthedocs.io/)
- Task lifecycle logging for [django-tasks](https://github.com/RealOrangeOne/django-tasks) and Django 6 native tasks
- Clean, type-safe API with comprehensive mypy typing

## Installation

Install the package using your package manager of choice:

```sh
# Using uv (recommended)
uv pip install thelab-instrumentation

# Using pip
pip install thelab-instrumentation
```

Add the package to your Django `INSTALLED_APPS`:

```py
INSTALLED_APPS = [
    # ...
    'thelabinstrumentation',
    'thelabinstrumentation.rq',        # Include if using RQ monitoring
    'thelabinstrumentation.structlog',  # Include if using django-structlog
    # ...
]
```

### Optional Dependencies

Install extras for the integrations you need:

```sh
# For RQ monitoring
uv pip install 'thelab-instrumentation[rq]'

# For structured logging
uv pip install 'thelab-instrumentation[structlog]'

# For django-tasks lifecycle logging
uv pip install 'thelab-instrumentation[tasks]'
```

## Configuration

Configure the library in your Django settings:

```py
THELAB_INSTRUMENTATION = {
    # Metrics backend (default: logging backend)
    'BACKEND': 'thelabinstrumentation.backends.cloudwatch.CloudWatchBackend',

    # Backend-specific options
    'OPTIONS': {
        # Cloudwatch Backend
        "namespace": 'MyApplication',
    },

    # Update interval in seconds (default: 60)
    'UPDATE_INTERVAL': 60,

    # Global dimensions added to all metrics
    'DIMENSIONS': {
        'Environment': 'production',
        'Application': 'my-app',
    },

    # Request headers to bind to structlog context (header name -> context var name)
    'STRUCTLOG_REQUEST_HEADERS': {
        'x-amz-cf-id': 'cf_id',
        'x-amzn-trace-id': 'x_amzn_trace_id',
    },
}
```

### Structlog Integration

The `thelabinstrumentation.structlog` app provides:

**HeaderBindingMiddleware** — Reads configured request headers and binds them to structlog contextvars. Must be placed **before** `django_structlog.middlewares.RequestMiddleware` so that bound headers are included in the `request_started` log event.

**QueryStatsMiddleware** — Tracks per-request database query count and total query duration, binding them as `db_query_count` and `db_query_duration_ms` to structlog contextvars. Must be placed **after** `django_structlog.middlewares.RequestMiddleware` so that the stats are bound before `request_finished` is logged. Uses Django's `connection.execute_wrapper()` API internally, so it works with any database backend without configuration changes.

```py
MIDDLEWARE = [
    # ...
    'thelabinstrumentation.structlog.middleware.HeaderBindingMiddleware',
    'django_structlog.middlewares.RequestMiddleware',
    'thelabinstrumentation.structlog.db.QueryStatsMiddleware',
    # ...
]
```

The headers to bind are configured via `STRUCTLOG_REQUEST_HEADERS` in `THELAB_INSTRUMENTATION` (see above). Each key is an HTTP header name and each value is the structlog context variable name it maps to.

**bind_username** — A signal receiver that automatically binds the authenticated user's username to structlog context. It connects to `django_structlog.signals.bind_extra_request_metadata` when the app is loaded — no manual wiring needed.

**Task lifecycle logging** — Signal receivers for `task_enqueued`, `task_started`, and `task_finished` that log task metadata to structlog context. Compatible with both [django-tasks](https://github.com/RealOrangeOne/django-tasks) (backport for Django 5.x) and Django 6's native `django.tasks`. Connected automatically when the app is loaded and a tasks package is available.

## Development

### Setup Development Environment

```sh
# Clone the repository
git clone https://gitlab.com/thelabnyc/thelab-instrumentation.git
cd thelab-instrumentation

# Install dependencies
uv sync

# Install pre-commit hooks
pre-commit install
```

### Run Tests

```sh
# Run all tests
uv run tox

# Run mypy type checking
uv run mypy thelabinstrumentation/

# Run linting
uv run ruff check
```
