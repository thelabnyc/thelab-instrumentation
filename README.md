# thelab-instrumentation

[![Latest Release](https://gitlab.com/thelabnyc/thelab-instrumentation/-/badges/release.svg)](https://gitlab.com/thelabnyc/thelab-instrumentation/-/releases)
[![pipeline status](https://gitlab.com/thelabnyc/thelab-instrumentation/badges/master/pipeline.svg)](https://gitlab.com/thelabnyc/thelab-instrumentation/-/commits/master)
[![coverage report](https://gitlab.com/thelabnyc/thelab-instrumentation/badges/master/coverage.svg)](https://gitlab.com/thelabnyc/thelab-instrumentation/-/commits/master)

A fully type-safe instrumentation and monitoring library for Django projects. This package provides:

- Metrics collection and reporting to various backends (CloudWatch, Logging)
- RQ queue monitoring
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
    'thelabinstrumentation.rq',  # Include if using RQ monitoring
    # ...
]
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
}
```

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
