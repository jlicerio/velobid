# VeloBid Agent Orientation

> Quick map for Codex, OpenCode, Hermes, and other agents working in this repo.
> Read this first when you need to understand where the live app runs, what to deploy, and which files own the current UI.

## What Is Live

- Live app: `https://velobid.tailfceaca.ts.net/`
- Deployment host: Linux host Docker directly
- Primary deploy path: `scripts/linux-host-deploy.sh`
- Compose file: `docker-compose.host.yml`
- Persistent host storage: `/srv/velobid`

## What To Use For Current State

- `docs/runbook-linux-no-vm.md`
  - Current deployment runbook
  - Describes init, deploy, health checks, backup, and restore
- `docs/DOCUMENTATION_STATUS.md`
  - Tells you which docs are current and which are archived
- `docs/README.md`
  - Index of the major docs

## Where The Important UI Lives

- Projects list: `frontend/src/pages/ProjectsPage.tsx`
- Project detail: `frontend/src/pages/ProjectDetailPage.tsx`
- Chat shell: `frontend/src/components/shared/AppShell.tsx`
- Chat panel: `frontend/src/components/chat/chat-panel.tsx`
- Chat messages: `frontend/src/components/chat/chat-message.tsx`
- Portfolio snapshot: `frontend/src/components/chat/dashboard-snapshot.tsx`
- Markdown rendering: `frontend/src/components/chat/markdown-content.tsx`

## What Agents Should Check Before Editing

1. Confirm whether the change is UI, API, or deployment.
2. Look for the active branch and worktree first.
3. Review the runbook if the change affects deployment or health checks.
4. Do not edit archived docs unless you are explicitly restoring history.
5. Preserve unrelated user changes in dirty worktrees.

## Deploy Workflow

1. Make the change in a branch or worktree.
2. Run local verification if possible.
3. Push the branch to `origin`.
4. On the Linux host, pull that branch and run:

```bash
sudo bash scripts/linux-host-deploy.sh
```

5. Verify:
   - `http://127.0.0.1:8000/api/v1/health`
   - `http://127.0.0.1:8644/v1/models`
   - The live `projects` page in the browser

## Useful Status Signals

- `velobid` container should be healthy.
- `hermes` container should be healthy.
- Archived projects should stay hidden from the default projects view.
- Assistant context should render as structured UI, not a raw text blob.

