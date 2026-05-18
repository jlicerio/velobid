# VeloBid Testing Guide

## Backend Tests (Python)

### Prerequisites

```bash
pip install -r requirements.txt
```

### Run backend tests

```bash
# Run all backend tests
pytest -q tests

# Run with coverage
pytest --cov=api --cov-report=term tests/

# Run a specific test module
pytest -q tests/test_auth_schemas.py

# Run a specific test
pytest -q tests/test_auth_schemas.py::TestSignupStartRequest::test_valid_payload
```

### Test categories

| Module | What it covers |
|--------|---------------|
| `tests/test_auth_schemas.py` | Signup request schema validation |
| `tests/test_validation.py` | Input validation rules |
| `tests/test_turnstile.py` | Turnstile verification (async, needs `pytest-asyncio`) |

## Frontend UI Smoke Tests (Playwright)

### Prerequisites

```bash
cd frontend
npm install        # Install all deps including @playwright/test
npx playwright install chromium  # Install browser binaries
```

### Configuration

Target URL is set via `VELOBID_URL` environment variable:

```bash
# Test against local dev
VELOBID_URL=http://localhost:8000 npx playwright test

# Test against deployed instance (default)
VELOBID_URL=http://192.168.1.237:8000 npx playwright test
```

### Run smoke tests

```bash
cd frontend

# Quick smoke (Chromium only)
npm run test:smoke

# Full smoke (all browsers)
npm run test:smoke:all

# All tests including auth flow
npm run test:e2e

# View HTML report
npm run test:report
```

### Test specs

| File | What it covers |
|------|---------------|
| `tests/smoke/login.spec.ts` | Login page rendering, field visibility, signup navigation |
| `tests/smoke/signup.spec.ts` | Signup form, validation, happy path to email-sent screen |
| `tests/smoke/health.spec.ts` | Backend health endpoints, frontend static asset serving |
| `tests/smoke/auth-flow.spec.ts` | Full login flow with valid/invalid credentials |

### Environment variables for tests

| Variable | Purpose |
|----------|---------|
| `VELOBID_URL` | Target app URL (default: `http://192.168.1.237:8000`) |
| `VELOBID_TEST_USER_ID` | Valid user ID for authenticated flow tests |
| `VELOBID_TEST_PASSWORD` | Valid password for authenticated flow tests |
| `CI` | When set, enables retries and single-worker mode |

### Example: CI pipeline run

```bash
CI=true VELOBID_URL=http://192.168.1.237:8000 npm run test:smoke:all
```

## Docker Smoke Test

From the project root on the Linux host:

```bash
# Makefile smoke test
make test
```

This runs:
- Health check against VeloBid API
- Health check against Hermes gateway
- Admin server health
- Chat echo test

## Known Issues & Workarounds

### `pytest-asyncio` missing

If you see:

```text
async def functions are not natively supported.
```

Install the async plugin:

```bash
pip install pytest-asyncio
```

It is now in `requirements.txt` on this branch.

### Frontend build on Windows UNC paths

`npm run build` and `npm run lint` may fail when the repo is accessed via UNC path (`\192.168.1.237\...`). Run frontend build/lint on the Linux host or a local drive.

### Playwright on remote

Playwright tests use HTTP requests against the deployed app. They do **not** spin up a local dev server. Ensure the target URL is reachable before running tests.
