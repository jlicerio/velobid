# VeloBid — Production Next Phase Plan

> Generated: 2026-05-18
> Based on: codebase sweep, live app smoke, PR/issue inventory, OpenAPI surface, deploy runbooks, browser MCP smoke, and repo/worktree audit.
> Authoritative for the next development phase.

---

## Table of Contents

1. [Current production state](#1-current-production-state)
2. [Live app health](#2-live-app-health)
3. [Repository topology](#3-repository-topology)
4. [GitHub PR and issue inventory](#4-github-pr-and-issue-inventory)
5. [Backend production surface](#5-backend-production-surface)
6. [Frontend production surface](#6-frontend-production-surface)
7. [Browser smoke test results](#7-browser-smoke-test-results)
8. [Production blockers and risks](#8-production-blockers-and-risks)
9. [Phase 2 workstream definition](#9-phase-2-workstream-definition)
10. [Recommended sequence](#10-recommended-sequence)

---

## 1. Current Production State

| Attribute | Value |
|---|---|
| Production URL | `http://192.168.1.237:8000` |
| Tailscale Funnel | `https://velobid.tailfceaca.ts.net/` |
| Deploy path | Linux host Docker directly (Phase 1) |
| Host storage | `/srv/velobid/` |
| Docker compose | `docker-compose.host.yml` |
| Hermes binding | `127.0.0.1:8644` |
| Frontend building | manual step in deploy workflow |
| Auth model | Legacy bidder JWT (frontend) + new email/password/2FA (backend scaffold) |
| Billing | scaffolded, `STRIPE_ENABLED=false` |
| Agent access | trial + rate limits implemented |
| CI | Hermes deploy only on push to `main` or `feat/**` |
| Test coverage | 29/31 backend pytest pass; Playwright scaffold created in PR #8 |

## 2. Live App Health

| Endpoint | Status | Response |
|---|---|---|
| `GET /api/v1/health` | `200` | `{"status":"ok","service":"velobid-api"}` |
| `GET /api/v1/meta` | `200` | `{"project_root":"/app","bid_projects_dir":"/data/velobid/bids"}` |
| `GET /` | `200` | redirects to `/login` |

### Console noise

```
401 on /api/v1/projects/with-pricing - app fetches before auth on page load
```

This is cosmetic but should be fixed to avoid polluting monitoring in production.

## 3. Repository Topology

### Worktrees

| Path | Branch | Status |
|---|---|---|
| `velobid` | `feat/signup-hardening-hermes` | synced with `origin`, clean working tree |
| `velobid-integrations` | `feat/integrations-composio` | synced with `origin` |
| `velobid-ui-tests` | `test/ui-playwright-smoke` | PR #8 |
| `/home/selfsim/projects/velobid-phase-next` | `phase/next-functionality` | prunable from Windows |

### Local branches

| Branch | Tracks | Behind | Ahead | Notes |
|---|---|---|---|---|
| `main` | `origin/main` | `0` | `0` | production baseline |
| `feat/signup-hardening-hermes` | `origin/feat/...` | `0` | `0` | active work, clean |
| `feat/integrations-composio` | `origin/feat/...` | `0` | `0` | worktree |
| `test/ui-playwright-smoke` | `origin/test/...` | `0` | `0` | PR #8 |
| `codex/container-sync-repo` | `origin/codex/...` | `0` | `0` | PR #7 |
| `phase/next-functionality` | `origin/phase/...` | `0` | `0` | PR #4 merged |
| `chore/hermes-deploy-workflow` | `origin/main` | `9` | `0` | stale, can be deleted |

## 4. GitHub PR and Issue Inventory

### Open pull requests

| PR | Title | State | Mergeable | Notes |
|---|---|---|---|---|
| #8 | test: Playwright UI smoke tests and backend async test support | OPEN | MERGEABLE | Needs lockfile update |
| #6 | [codex] auto-open project bid workspace | OPEN draft | MERGEABLE | Single file, +7 lines |
| #7 | chore: sync container workflow and agent tooling | OPEN draft | CONFLICTING | 58 files, too broad |

### Merged PRs

| PR | Title |
|---|---|
| #4 | fix: robust AI chat error handling |

No open issues.

## 5. Backend Production Surface

OpenAPI exposes **54 routes** across auth, bids, projects, chat, billing, files, blueprints, vision, residential, settings, sessions, trades, integrations, and sync.

See `/openapi.json` on the running instance for the full route inventory.

## 6. Frontend Production Surface

Pages implemented: login, signup, terms, privacy, projects dashboard, project detail, document viewer, blueprint vision, residential estimates, settings (with tabs for profile, bidders, users, trades), and 404.

Chat sidebar with SSE streaming, STT/TTS, markdown rendering, and mobile-responsive layout.

## 7. Browser Smoke Test Results

All tests performed against live deployed app:

```
16 / 16 PASS - 0 FAIL
```

## 8. Production Blockers and Risks

### 8.1 Auth model is split
### 8.2 Pending signup state in memory (lost on restart)
### 8.3 Default JWT secrets in code
### 8.4 CORS is wildcard
### 8.5 Dockerfile does not build frontend
### 8.6 No CI on main branch
### 8.7 PR #7 conflates many changes
### 8.8 Playwright lockfile may need update
### 8.9 Backend tests need pytest-asyncio
### 8.10 QA artifacts remain on host
### 8.11 Hermes health not remotely verifiable

## 9. Phase 2 Workstream Definition

The next development phase is **Production Beta Hardening**.

Goal: Move from "functional single-node beta" to "safe, testable, deployable production beta."

| Workstream | Priority | Focus |
|---|---|---|
| A - Test gate and CI | Highest | PR #8 completion, GitHub Actions CI, Docker build workflow |
| B - Auth/signup productionization | High | Durable storage for signups, env validation |
| C - Deploy image reproducibility | High | Multi-stage Dockerfile with frontend build |
| D - Security hardening | High | CORS allowlist, startup validation, security headers |
| E - Release QA automation | Medium | Playwright tests for release checklist |
| F - Billing and agent access | Medium | Stripe E2E, 402/429 UX |
| G - PR/branch hygiene | Medium | Merge/close PRs, delete stale branches |

## 10. Recommended Sequence

### Immediate (this week)

1. Complete PR #8 (lockfile, Linux install, verify)
2. Clean QA artifacts on host
3. Review and merge PR #6

### Next (within 2 weeks)

4. Create CI branch with GitHub Actions
5. Create security hardening branch
6. Create multi-stage Dockerfile branch

### After CI + Security + Build

7. Auth production persistence
8. Release QA automation
9. Split and merge PR #7 sub-PRs
10. Billing beta readiness

## Appendix - Quick Reference Commands

```bash
# Check Hermes health on host
curl -fsS -H "Authorization: Bearer $(grep '^HERMES_API_KEY=' /srv/velobid/secrets/velobid.env | cut -d= -f2-)" http://127.0.0.1:8644/v1/models

# Clean QA artifacts
sudo rm -rf /home/selfsim/projects/velobid/config/bidders/qa_*

# Run backend tests
pip install -r requirements.txt && pytest -q tests

# Run frontend Playwright smoke
cd /home/selfsim/projects/velobid-ui-tests/frontend
npm install && npx playwright install chromium
VELOBID_URL=http://192.168.1.237:8000 npm run test:smoke
```
