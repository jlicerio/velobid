# VeloBid Testing Guide

This is the canonical entrypoint for validation and smoke checks.

## Unit checks

Run the project unit tests:

```bash
python scripts/verify.py
```

Or, via Make:

```bash
make verify
```

This currently runs the core validator suite in `tests/test_validation.py`.

## Live smoke checks

Run the backend smoke gate against the host stack:

```bash
python scripts/verify.py --live
```

Or:

```bash
make smoke
```

If you are running the dev-sync frontend on `http://127.0.0.1:5173`, include it too:

```bash
python scripts/verify.py --live --frontend-url http://127.0.0.1:5173
```

Or:

```bash
make smoke-dev
```

## Existing test files

- `tests/test_validation.py`: primary pytest unit suite
- `qa_test_suite.py`: legacy all-in-one QA script, retained for historical reference
- `server_test.py`: legacy server smoke script, retained for historical reference

Prefer `scripts/verify.py` for new validation work so the repo has one obvious test entrypoint.
