> **ARCHIVED** — Historical run report for Kaban + OpenCode automation from 2026-05-08. Superseded by current deployment; key takeaway (Linux host Docker redeploy on selfsim@192.168.1.237) is documented in the active runbook.
> This document has been archived because its purpose has been fulfilled or superseded by newer documentation.
> See  for the current development plan.
> Original location: 
# Kaban + OpenCode Run Report (2026-05-08)

## Summary

This run completed the queued Kaban automation tasks and deployed the updated stack on the Linux SSH host.

- Date: 2026-05-08
- Host: `selfsim@192.168.1.237`
- Repo path: `/home/selfsim/projects/velobid`
- Deployment command: `docker compose up -d --build`

## Completed Kaban Tasks

The following tasks were completed by the OpenCode loop:

1. `Run full projects dashboard UI audit and fix regressions`
2. `Add dashboard export: portfolio summary CSV`
3. `Add bulk project actions: archive/unarchive selected projects`

## Loop Reliability Fixes

`scripts/opencode-kaban-loop.ps1` was hardened to prevent stalled runs:

1. Replaced ambiguous `$Args` usage with explicit `-CommandArgs` in Kaban command calls.
2. Added robust JSON extraction/parsing with defensive logging for malformed CLI output.
3. Normalized task selection to always produce an array, including single-task `todo` states.
4. Added exception recovery to move the active task back to `todo` if runtime failures occur.

## Deployment Result

After rebuild and restart on the Linux host:

- `velobid` container: healthy
- `hermes` container: healthy

Validation command used:

```bash
docker compose ps
```

## Notes

- The OpenCode Kaban loop was intentionally stopped after queue completion.
- Existing tailscale-related containers were left running as-is.
