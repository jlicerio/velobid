> **ARCHIVED** — Historical execution report for the no-VM Linux host runbook from 2026-05-06. The runbook itself is still active; this report documents a specific execution session and can be referenced for historical context.
> This document has been archived because its purpose has been fulfilled or superseded by newer documentation.
> See  for the current development plan.
> Original location: 
# VeloBid No-VM Linux Host Runbook Execution Report

Date: 2026-05-06 (local) / 2026-05-07 UTC
Runbook: docs/runbook-linux-no-vm.md
Executor: automated agent execution

## Final Status: SUCCESS

## Commands Run

1. `cd /home/selfsim/projects/velobid && sudo bash scripts/linux-host-init.sh`
   - Result: /srv/velobid initialized, config/bid_projects seeded, env file created

2. `sudo bash -c 'source /srv/velobid/secrets/velobid.env && ...'` (verification checks)
   - Result: HERMES_API_KEY, HERMES_CREDENTIALS_JSON, VELOBID_BIND_ADDR, HERMES_BIND_ADDR verified present

3. `cd /home/selfsim/projects/velobid && docker compose -f docker-compose.yml down`
   - Result: old volume-based stack removed to avoid container-name conflicts

4. `cd /home/selfsim/projects/velobid && sudo bash scripts/linux-host-deploy.sh`
   - Result: images built, containers started, health checks passed

5. `curl -fsS http://127.0.0.1:8000/api/v1/meta`
   - Result: PASS (200, project_root and bid_projects_dir returned)

6. `curl -fsS http://127.0.0.1:8000/api/v1/health`
   - Result: PASS (200, status ok)

7. `curl -fsS -H "Authorization: Bearer <redacted>" http://127.0.0.1:8644/v1/models`
   - Result: PASS (200, model list returned)

8. `sudo docker compose --env-file /srv/velobid/secrets/velobid.env -f docker-compose.host.yml ps`
   - Result: PASS (both services healthy)

9. `cd /home/selfsim/projects/velobid && sudo bash scripts/linux-host-backup.sh`
   - Result: /srv/velobid/backups/velobid-20260507T045148Z.tar.gz + .sha256 created

## Blockers Encountered

### Blocker 1: Sudo authentication
- `sudo -n true` initially failed (no cached credential).
- Resolution: direct `sudo` commands succeeded after a brief auth cache; no interactive password prompt was required during execution.
- User action required: none.

### Blocker 2: Missing environment variables in seeded env file
- The seed file (env.production.example) did not include `OPENCODE_API_KEY`, `OPENCODE_BASE_URL`, `DEEPSEEK_MODEL`, `JWT_SECRET`, `XAI_API_KEY`, `XAI_BASE_URL`, or `XAI_VISION_MODEL`.
- First deploy failed with: `openai.OpenAIError: Missing credentials` because the VeloBid API container could not initialize its OpenAI client.
- Resolution: copied missing keys from the existing project `.env` into `/srv/velobid/secrets/velobid.env`, redeployed, and all health checks passed.
- User action required: none.

## Verification Summary

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| VeloBid API meta | 200 | 200 | PASS |
| VeloBid health | 200 | 200 | PASS |
| Hermes gateway models | 200 + model list | 200 + model list | PASS |
| Docker Compose PS | both healthy | both healthy | PASS |
| Backup file | .tar.gz + .sha256 | both present | PASS |

## Artifacts

- Backup: /srv/velobid/backups/velobid-20260507T045148Z.tar.gz
- Backup checksum: /srv/velobid/backups/velobid-20260507T045148Z.tar.gz.sha256
- Host storage: /srv/velobid/ (config, bid_projects, data, hermes, backups, secrets)
- Env file: /srv/velobid/secrets/velobid.env (permissions 600, required values present)

## Notes

- Old docker-compose.yml stack (using Docker volumes) was gracefully removed before switching to the host-bind mount stack.
- The `curl: (56) Recv failure: Connection reset by peer` transient error during deploy-script Hermes check resolved on retry; manual verification confirmed the gateway is healthy.
- No restic offsite backup configured (RESTIC_REPOSITORY not set); only local backup was produced.
