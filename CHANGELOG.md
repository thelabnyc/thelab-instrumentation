# Changes

## v0.7.0 (2026-10-30)

### Feat

- test Django 6.1
- support Python 3.15 and drop Python 3.13

### Fix

- **deps**: update dependency django-structlog to >=11.0.0
- **deps**: update dependency sentry-sdk to >=2.73.0
- **deps**: update boto to >=1.43.118
- **deps**: update boto to >=1.43.114
- **deps**: update dependency sentry-sdk to >=2.72.0
- **deps**: update boto to >=1.43.110
- **deps**: update boto to >=1.43.107
- **deps**: update dependency sentry-sdk to >=2.71.0
- **deps**: update boto to >=1.43.102
- **deps**: update dependency sentry-sdk to >=2.70.0
- **deps**: update boto to >=1.43.97
- **deps**: update dependency urllib3 to >=2.8.0
- **deps**: update dependency sentry-sdk to >=2.69.2
- **deps**: update boto to >=1.43.92
- **deps**: update dependency sentry-sdk to >=2.69.1
- **deps**: update dependency sentry-sdk to >=2.69.0
- **deps**: update boto to >=1.43.88
- **deps**: update dependency rq to >=2.12.0
- **deps**: update dependency django-rq to >=4.2.0
- **deps**: update boto to >=1.43.82
- **deps**: update dependency sentry-sdk to >=2.68.1
- **deps**: update boto to >=1.43.77
- **deps**: update dependency rq to >=2.11.0
- **deps**: update boto to >=1.43.71
- **deps**: update dependency sentry-sdk to >=2.68.0
- **deps**: update dependency sentry-sdk to >=2.67.1
- **deps**: update boto to >=1.43.66
- **deps**: update boto to >=1.43.61
- **deps**: update boto to >=1.43.55
- **deps**: update dependency sentry-sdk to >=2.66.1
- **deps**: update boto to >=1.43.50
- **deps**: update dependency sentry-sdk to >=2.66.0
- **deps**: update dependency sentry-sdk to >=2.65.0
- **deps**: update boto to >=1.43.45
- **deps**: update dependency django-rq to >=4.1.1
- **deps**: update dependency typing-extensions to >=4.16.0
- **deps**: update boto to >=1.43.40
- **deps**: update dependency sentry-sdk to >=2.64.0
- **deps**: update boto to >=1.43.36
- **deps**: update dependency sentry-sdk to >=2.63.0
- **deps**: update dependency rq to >=2.10.0
- **deps**: update boto to >=1.43.33
- **deps**: update boto to >=1.43.28
- **deps**: update dependency sentry-sdk to >=2.62.0
- **deps**: update dependency rq to >=2.9.1
- **deps**: update boto to >=1.43.23
- **deps**: update dependency sentry-sdk to >=2.61.1
- **deps**: update dependency django-structlog to >=10.1.0
- **deps**: update dependency sentry-sdk to >=2.61.0
- **deps**: update boto to >=1.43.17
- **deps**: update boto to >=1.43.13
- **deps**: update dependency rq to >=2.9.0
- **deps**: update boto to >=1.43.8
- **deps**: update dependency sentry-sdk to >=2.60.0
- **deps**: update dependency urllib3 to >=2.7.0
- **deps**: update boto to >=1.43.6
- **deps**: update dependency sentry-sdk to >=2.59.0
- **deps**: update boto to >=1.43.1
- **deps**: update boto to >=1.42.95
- **deps**: update dependency rq to >=2.8.0
- **deps**: update boto to >=1.42.90
- **deps**: update dependency sentry-sdk to >=2.58.0

### Refactor

- adopt Python 3.14 syntax

## v0.6.4 (2026-04-16)

### Fix

- forward positional arguments to `_original_urlopen` in `outgoing_http`
- **deps**: update boto to >=1.42.87

## v0.6.3 (2026-04-09)

### Fix

- **rq**: reduce noise from RQ daemon when Redis is unavailable
- **deps**: update dependency django-rq to >=4.1.0
- **deps**: update boto to >=1.42.82
- **deps**: update dependency sentry-sdk to >=2.57.0

## v0.6.2 (2026-03-31)

### Fix

- django-stubs versions
- **deps**: update boto to >=1.42.77
- **deps**: update dependency urllib3 to >=2.6.3
- **deps**: update dependency django-stubs-ext to >=6.0.1,<7

## v0.6.1 (2026-03-27)

### Fix

- django stubs version

## v0.6.0 (2026-03-27)

### Feat

- log timing and success of all outgoing HTTP requests

### Fix

- **deps**: update dependency sentry-sdk to >=2.56.0
- **deps**: update boto to >=1.42.72
- **deps**: update dependency sentry-sdk to >=2.55.0
- **deps**: update dependency django-stubs-ext to >=6.0.1
- **deps**: update dependency django-stubs-ext to >=6.0.0
- **deps**: update dependency django-rq to >=4.0.1
- **deps**: update dependency django-rq to >=4.0.0
- **deps**: update boto to >=1.42.67
- **deps**: update boto to >=1.42.62
- **deps**: update dependency sentry-sdk to >=2.54.0
- **deps**: update boto to >=1.42.58
- **deps**: update dependency rq to >=2.7.0

## v0.5.0 (2026-02-24)

### Feat

- add StructlogBackend for metrics
- add QueryStatsMiddleware for per-request DB query stats
- add django-structlog helpers and task lifecycle logging

### Fix

- **deps**: update dependency django-tasks to >=0.12.0
- **deps**: update dependency django-structlog to >=10.0.0
- code review rework
- **deps**: update dependency sentry-sdk to >=2.53.0
- **deps**: update boto to >=1.42.43
- **deps**: update dependency sentry-sdk to >=2.52.0

## v0.4.0 (2026-02-06)

### Feat

- support Python 3.14

### Fix

- avoid signal handling in background thread for RQ metrics
- **deps**: update dependency sentry-sdk to >=2.51.0
- **deps**: update boto to >=1.42.38
- **deps**: update boto to >=1.42.33
- **deps**: update dependency django-stubs-ext to >=5.2.9
- **deps**: update dependency sentry-sdk to >=2.50.0
- **deps**: update boto to >=1.42.29
- **deps**: update dependency sentry-sdk to >=2.49.0
- **deps**: update boto to >=1.42.24
- **deps**: update boto to >=1.42.19
- **deps**: update boto to >=1.42.16
- **deps**: update dependency django-rq to >=3.2.2
- **deps**: update dependency sentry-sdk to >=2.48.0
- **deps**: update boto to >=1.42.13
- **deps**: update boto to >=1.42.8
- **deps**: update dependency sentry-sdk to >=2.47.0
- **deps**: update boto to >=1.42.3
- **deps**: update dependency django-stubs-ext to >=5.2.8
- **deps**: update boto to >=1.41.5
- **deps**: update dependency django-rq to >=3.2.1
- **deps**: update dependency sentry-sdk to >=2.46.0
- **deps**: update dependency django-rq to >=3.2.0
- **deps**: update dependency rq to >=2.6.1
- **deps**: update boto to >=1.41.1
- **deps**: update dependency sentry-sdk to >=2.45.0
- **deps**: update boto to >=1.40.73
- **deps**: update dependency sentry-sdk to >=2.44.0
- **deps**: update dependency sentry-sdk to >=2.43.0
- **deps**: update boto to >=1.40.58
- **deps**: update dependency sentry-sdk to >=2.42.1
- **deps**: update dependency sentry-sdk to >=2.42.0
- **deps**: update dependency sentry-sdk to >=2.41.0
- **deps**: update dependency django-stubs-ext to >=5.2.7
- **deps**: update dependency django-stubs-ext to >=5.2.6
- **deps**: update boto to >=1.40.44
- **deps**: update dependency sentry-sdk to >=2.39.0
- **deps**: update boto to >=1.40.39
- **deps**: update boto to >=1.40.34
- **deps**: update dependency sentry-sdk to >=2.38.0
- **deps**: update dependency django-stubs-ext to >=5.2.5
- **deps**: update dependency django-stubs-ext to >=5.2.4
- **deps**: update boto to >=1.40.29
- **deps**: update dependency sentry-sdk to >=2.37.1
- **deps**: update dependency rq to >=2.6.0
- **deps**: update dependency sentry-sdk to >=2.37.0
- **deps**: update boto to >=1.40.24
- **deps**: update dependency sentry-sdk to >=2.36.0
- **deps**: update dependency sentry-sdk to >=2.35.2
- **deps**: update dependency typing-extensions to >=4.15.0
- **deps**: update dependency rq to >=2.5.0
- **deps**: update dependency sentry-sdk to >=2.35.1
- **deps**: update dependency django-stubs-ext to >=5.2.2
- **deps**: update dependency django-rq to >=3.1
- prevent renovate from pointing all URLs at gitlab

### Refactor

- migrate black/flake8 -> ruff

## v0.3.0 (2025-06-25)

### Feat

- add new metrics rq.finished-jobs, rq.workers, rq.queued-jobs-per-worker

### Fix

- fix sentry-sdk dep

## v0.2.1 (2025-06-25)

### Fix

- remove runtime dependency on mypy_boto3_cloudwatch
- make logging backend ignore unknown kwargs

## v0.2.0 (2025-06-25)

### Feat

- initial commit

### Fix

- only track queue depth for now
