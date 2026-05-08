# Hermes Delegation Runbook

This project includes local wrappers that call the `codex-to-hermes` plugin scripts from Windows PowerShell.

## Files
- `scripts/hermes-delegate.ps1`: main wrapper for prompt delegation and Hermes command mode.
- `scripts/hermes-smoke.ps1`: quick connectivity smoke test wrapper.

## Prerequisite

By default, wrappers look for the plugin at:

`C:\Users\xlice\plugins\codex-to-hermes`

Legacy fallback is still supported:

`C:\Users\xlice\Desktop\skills\codex-to-hermes`

If your skill is elsewhere, set:

```powershell
$env:CODEX_HERMES_SKILL_ROOT = "C:\path\to\codex-to-hermes"
```

## 1) Verify Hermes access

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\hermes-smoke.ps1
```

Expected markers include `SSH_OK`, `HERMES_VERSION_OK`, and `HERMES_SMOKE_OK`.

## 2) Delegate a repo-aware task

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\hermes-delegate.ps1 `
  -ProjectPath /home/selfsim/projects/velobid `
  -Prompt "Inspect the current branch, run fast tests, and summarize failures only."
```

## 3) Run Hermes subcommands

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\hermes-delegate.ps1 `
  -HermesArgs @('status')

powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\hermes-delegate.ps1 `
  -HermesArgs @('kanban','list')
```

## 4) Create a Hermes kanban task

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\hermes-delegate.ps1 `
  -HermesArgs @(
    'kanban','create',
    'Investigate estimate flow regression in velobid',
    '--assignee','codex',
    '--priority','3'
  )
```

## 5) Debug connection fallback

Add `-PrintConnection` to show the active connection path:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\hermes-delegate.ps1 `
  -Prompt "Say only OK" `
  -PrintConnection
```

## Recommended delegation pattern
- Keep Codex local for planning, patch review, and final summaries.
- Send Linux execution tasks to Hermes with explicit expected outputs.
- For long-running work, require Hermes to return command, PID or task id, log path, and verification command.
