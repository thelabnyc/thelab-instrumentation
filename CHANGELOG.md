# Changes

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
