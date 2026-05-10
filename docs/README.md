# VeloBid Documentation Index

This directory contains all project documentation. Files are grouped by purpose and currency. Nothing is deleted — superseded docs are moved to `archive/` with archive banners.

---

## Active

Docs you should read first for current operations.

| File | Purpose |
|------|---------|
| [container-sync-notes.md](container-sync-notes.md) | Short note on the dev-sync vs production container split and the host tree. |
| [development.md](development.md) | Dev-sync container workflow with mounted source, Vite HMR, and optional Hermes profile. |
| [testing.md](testing.md) | Canonical validation entrypoint and smoke-check commands. |
| [runbook-linux-no-vm.md](runbook-linux-no-vm.md) | **Primary deployment runbook.** Linux host Docker Compose path using `docker-compose.host.yml`, `/srv/velobid` storage, and `scripts/linux-host-*.sh`. |
| [stripe-billing-runbook.md](stripe-billing-runbook.md) | Configure Stripe Checkout, Customer Portal, webhook signing, and production env values for billing. |
| [kaban-opencode-run-report-2026-05-08.md](kaban-opencode-run-report-2026-05-08.md) | Run report for Kaban automation completion, loop hardening, and Linux host Docker redeploy on 2026-05-08. |

---

## Optional / Reference

Docs that are still valid but not part of the daily path.

| File | Purpose |
|------|---------|
| [phase1-to-phase2-user-data-cutover-checklist.md](phase1-to-phase2-user-data-cutover-checklist.md) | Future checklist for migrating from single-node Docker Compose to a scalable beta-ready architecture. Not yet in scope. |
| [hermes-delegation-runbook.md](hermes-delegation-runbook.md) | Windows PowerShell wrappers for delegating tasks to Hermes via `codex-to-hermes`. |
| [model-cost-delegation-playbook.md](model-cost-delegation-playbook.md) | Production playbook for low-cost model routing, token budgets, escalation triggers, and local-vs-Hermes delegation policy. |

---

## QA

Checklists and audit notes from QA passes.

| File | Purpose |
|------|---------|
| [qa-ui-audit-notes-2026-05-06.md](qa-ui-audit-notes-2026-05-06.md) | UI/UX regression notes from the 2026-05-06 pass. |
| [release-qa-checklist-2026-05-06.md](release-qa-checklist-2026-05-06.md) | Pre-prod signoff checklist used before promoting a build. |

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

---

## Quick Links

- **Dev sync:** `docker compose -f docker-compose.dev.yml up --build`
- **Deploy:** `scripts/linux-host-deploy.sh`
- **Verify:** `python scripts/verify.py`
- **Smoke:** `python scripts/verify.py --live`
- **Dev smoke:** `python scripts/verify.py --live --frontend-url http://127.0.0.1:5173`
- **Init storage:** `scripts/linux-host-init.sh`
- **Backup:** `scripts/linux-host-backup.sh`
- **Restore:** `scripts/linux-host-restore.sh`
- **Compose file:** `docker-compose.host.yml`
