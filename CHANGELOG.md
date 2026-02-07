# Changes

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
