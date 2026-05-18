# VeloBid Documentation Status

Last updated: 2026-05-18

## What is current

The active deployment path is **Linux host Docker directly**.

- **Primary runbook:** `docs/runbook-linux-no-vm.md`
  - Uses `docker-compose.host.yml`
  - Persists data under `/srv/velobid`
  - Managed by `scripts/linux-host-*.sh` (init, deploy, backup, restore)
  - Hermes runs containerized alongside VeloBid

- **Production plan:** `docs/production-next-phase-plan.md` is the primary reference for migrating to Phase 2 (scalable architecture, production readiness).

- **Architecture docs:** `docs/architecture.md` and `docs/hermes-multi-tenant-architecture.md` describe the running system and future multi-tenant design.

- **Feature docs:** `docs/features/dev-mode.md` describes the `DEV_MODE=true` bypass behavior in auth/signup for local development.

## What is archived

The following docs are kept for reference but are **not** the current path:

| Doc | Original purpose | Archived because |
|-----|-----------------|------------------|
| `docs/archive/phase1-finalization-runbook.md` | VM-based Phase 1 deployment (libvirt/KVM) | Superseded by Linux host Docker path |
| `docs/archive/hermes-docker-full-run-2026-05-06.md` | Deployment run report from a specific session | Historical record; procedures are now in the active runbook |
| `docs/archive/vm-bootstrap/` | Cloud-init pack for Ubuntu VM provisioning | VM path is no longer active |
| `docs/archive/kaban-opencode-run-report-2026-05-08.md` | Kaban queue run report and loop hardening | Historical run report, purpose fulfilled |
| `docs/archive/no-vm-runbook-execution-report-2026-05-06.md` | No-VM runbook execution report | Historical run report, purpose fulfilled |
| `docs/archive/tailscale-serve-velobid-2026-05-06.md` | Tailscale serve configuration notes | Tailscale config completed, historical |
| `docs/archive/tailscale-container-overlay-2026-05-07.md` | Tailscale container overlay approach | Was BLOCKED, not the current approach |
| `docs/archive/qa-ui-audit-notes-2026-05-06.md` | UI/UX regression audit from QA pass | Completed QA pass, issues fixed |
| `docs/archive/release-qa-checklist-2026-05-06.md` | Pre-prod signoff checklist | Superseded by production-next-phase-plan.md |

All archived files have archive banners at the top explaining their status and pointing to the current replacement.

## What is optional / future

| Doc | Purpose |
|-----|---------|
| `docs/phase1-to-phase2-user-data-cutover-checklist.md` | Checklist for a future migration to Phase 2 (scalable/multi-node). Not in scope today. |
| `docs/hermes-delegation-runbook.md` | Windows-side PowerShell wrappers for Hermes delegation. Used on demand, not part of deployment. |
| `docs/plans/social-auth-worktree.md` | Future plan for OAuth social login. Not yet implemented. |

## How to update this status

When the deployment path changes again:
1. Update this file.
2. Move superseded docs to `docs/archive/` and add an archive banner.
3. Update `docs/README.md` to reflect the new sections.
4. Do not delete old docs.
