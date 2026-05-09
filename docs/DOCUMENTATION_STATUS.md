# VeloBid Documentation Status

Last updated: 2026-05-08

## What is current

The active deployment path is **Linux host Docker directly**.

- **Primary runbook:** `docs/runbook-linux-no-vm.md`
  - Uses `docker-compose.host.yml`
  - Persists data under `/srv/velobid`
  - Managed by `scripts/linux-host-*.sh` (init, deploy, backup, restore)
  - Hermes runs containerized alongside VeloBid

- **Agent orientation:** `docs/agent-orientation.md`
  - Short map for workers and operators
  - Points to the live host, current deploy path, and key UI files
  - Helps agents find the right source of truth quickly

- **Architecture docs:** `docs/architecture.md` and `docs/hermes-multi-tenant-architecture.md` describe the running system and future multi-tenant design.

- **QA docs:** `docs/qa-ui-audit-notes-2026-05-06.md` and `docs/release-qa-checklist-2026-05-06.md` reflect the most recent QA pass.

- **Latest operations report:** `docs/kaban-opencode-run-report-2026-05-08.md`
  - Confirms Kaban queue completion for 3 dashboard tasks
  - Documents OpenCode loop reliability fixes in `scripts/opencode-kaban-loop.ps1`
  - Confirms successful Docker redeploy on `selfsim@192.168.1.237` at `/home/selfsim/projects/velobid`

## What is archived

The following docs are kept for reference but are **not** the current path:

| Doc | Original purpose | Archived because |
|-----|-----------------|------------------|
| `docs/archive/phase1-finalization-runbook.md` | VM-based Phase 1 deployment (libvirt/KVM) | Superseded by Linux host Docker path |
| `docs/archive/hermes-docker-full-run-2026-05-06.md` | Deployment run report from a specific session | Historical record; procedures are now in the active runbook |
| `docs/archive/vm-bootstrap/` | Cloud-init pack for Ubuntu VM provisioning | VM path is no longer active |

All archived files have archive banners at the top explaining their status and pointing to the current replacement.

## What is optional / future

| Doc | Purpose |
|-----|---------|
| `docs/phase1-to-phase2-user-data-cutover-checklist.md` | Checklist for a future migration to Phase 2 (scalable/multi-node). Not in scope today. |
| `docs/hermes-delegation-runbook.md` | Windows-side PowerShell wrappers for Hermes delegation. Used on demand, not part of deployment. |

## How to update this status

When the deployment path changes again:
1. Update this file.
2. Move superseded docs to `docs/archive/` and add an archive banner.
3. Update `docs/README.md` to reflect the new sections.
4. Do not delete old docs.
