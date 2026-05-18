# VeloBid Documentation Index

This directory contains all project documentation. Files are grouped by purpose and currency. Nothing is deleted — superseded docs are moved to `archive/` with archive banners.

---

## Active

Docs you should read first for current operations.

| File | Purpose |
|------|---------|
| [runbook-linux-no-vm.md](runbook-linux-no-vm.md) | **Primary deployment runbook.** Linux host Docker Compose path using `docker-compose.host.yml`, `/srv/velobid` storage, and `scripts/linux-host-*.sh`. |
| [production-next-phase-plan.md](production-next-phase-plan.md) | **Production plan.** Covers migration to Phase 2 scalable architecture and production readiness. Primary reference for what's next. |
| [stripe-billing-runbook.md](stripe-billing-runbook.md) | Configure Stripe Checkout, Customer Portal, webhook signing, and production env values for billing. |

---

## Optional / Reference

Docs that are still valid but not part of the daily path.

| File | Purpose |
|------|---------|
| [features/dev-mode.md](features/dev-mode.md) | Describes the `DEV_MODE=true` bypass behavior in auth/signup for local development. |
| [plans/social-auth-worktree.md](plans/social-auth-worktree.md) | Future plan for OAuth social login. Not yet implemented. |
| [phase1-to-phase2-user-data-cutover-checklist.md](phase1-to-phase2-user-data-cutover-checklist.md) | Future checklist for migrating from single-node Docker Compose to a scalable beta-ready architecture. Not yet in scope. |
| [hermes-delegation-runbook.md](hermes-delegation-runbook.md) | Windows PowerShell wrappers for delegating tasks to Hermes via `codex-to-hermes`. |
| [model-cost-delegation-playbook.md](model-cost-delegation-playbook.md) | Production playbook for low-cost model routing, token budgets, escalation triggers, and local-vs-Hermes delegation policy. |

---

## Architecture

Design docs and diagrams.

| File | Purpose |
|------|---------|
| [architecture.md](architecture.md) | High-level VeloBid architecture: data flow, key patterns, Mermaid diagram. |
| [hermes-multi-tenant-architecture.md](hermes-multi-tenant-architecture.md) | Multi-tenant Hermes design: containerized profiles, auto-creation, file management, K8s migration path. |
| [architecture-diagram.html](architecture-diagram.html) | Standalone HTML architecture diagram (dark-themed SVG rendered in browser). |

---

## Historical / Archived

Superseded runbooks, run reports, and the VM bootstrap pack. Kept for reference and disaster recovery.

| File | Why it was archived |
|------|-------------------|
| [archive/phase1-finalization-runbook.md](archive/phase1-finalization-runbook.md) | VM-based Phase 1 finalization (libvirt/KVM). Superseded by `runbook-linux-no-vm.md`. |
| [archive/hermes-docker-full-run-2026-05-06.md](archive/hermes-docker-full-run-2026-05-06.md) | Historical deployment run report from 2026-05-06. Documents the `entrypoint.sh` fix. |
| [archive/vm-bootstrap/](archive/vm-bootstrap/) | Full cloud-init VM bootstrap pack (user-data, meta-data, network-config, host runbook, verify script). The VM path is no longer active. |
| [archive/kaban-opencode-run-report-2026-05-08.md](archive/kaban-opencode-run-report-2026-05-08.md) | Kaban queue run report and loop hardening. Purpose fulfilled. |
| [archive/no-vm-runbook-execution-report-2026-05-06.md](archive/no-vm-runbook-execution-report-2026-05-06.md) | No-VM runbook execution report from 2026-05-06. Purpose fulfilled. |
| [archive/tailscale-serve-velobid-2026-05-06.md](archive/tailscale-serve-velobid-2026-05-06.md) | Tailscale serve configuration notes. Configuration completed. |
| [archive/tailscale-container-overlay-2026-05-07.md](archive/tailscale-container-overlay-2026-05-07.md) | Tailscale container overlay approach. Was BLOCKED, not the current approach. |
| [archive/qa-ui-audit-notes-2026-05-06.md](archive/qa-ui-audit-notes-2026-05-06.md) | UI/UX regression audit from the 2026-05-06 QA pass. Issues fixed. |
| [archive/release-qa-checklist-2026-05-06.md](archive/release-qa-checklist-2026-05-06.md) | Pre-prod signoff checklist. Superseded by `production-next-phase-plan.md`. |

---

## Quick Links

- **Deploy:** `scripts/linux-host-deploy.sh`
- **Init storage:** `scripts/linux-host-init.sh`
- **Backup:** `scripts/linux-host-backup.sh`
- **Restore:** `scripts/linux-host-restore.sh`
- **Compose file:** `docker-compose.host.yml`
