# Container Sync Notes

This note captures the current split between local development and Linux-host deployment.

## Current setup

- **Dev sync:** use `docker-compose.dev.yml` for mounted source, hot reload, and browser refreshes.
- **Production:** use `scripts/linux-host-deploy.sh` on the Linux host for the immutable container stack.

## Source of truth

- Repo docs: `docs/development.md`, `docs/testing.md`, and `docs/runbook-linux-no-vm.md`
- Verification: `python scripts/verify.py`
- Host tree: `/home/selfsim/velobid`

## Practical reminders

- Keep dev and production separate so the runtime containers stay clean.
- Keep legacy QA scripts only as references unless a workflow still depends on them.
- If the host tree drifts from git, sync the repo changes over before redeploying.

