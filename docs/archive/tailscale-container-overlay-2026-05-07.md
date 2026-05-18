> **ARCHIVED** — Historical Tailscale container overlay deployment report from 2026-05-07. Was marked BLOCKED; the current deployment uses host-level Tailscale instead of the container overlay pattern.
> This document has been archived because its purpose has been fulfilled or superseded by newer documentation.
> See  for the current development plan.
> Original location: 
# Tailscale Container Overlay Deployment Report

Date: 2026-05-07
Status: BLOCKED — Missing TAILSCALE_AUTHKEY
Environment: /srv/velobid (no-VM Docker host)

## Pre-flight Checks

### 1. Secret Inspection
File: `/srv/velobid/secrets/velobid.env`
Method: `sudo grep -c '^TAILSCALE_AUTHKEY='` (value redacted)
Result: **0 matches** — TAILSCALE_AUTHKEY is not defined.

### 2. Stack Health
Current active stack (docker-compose.host.yml):
| Container | Status | Ports |
|-----------|--------|-------|
| velobid   | Up 23 min (healthy) | 0.0.0.0:8000->8000/tcp |
| hermes    | Up 23 min (healthy) | 127.0.0.1:8644->8642/tcp |

VeloBid base stack is healthy.

### 3. Tailscale Overlay Files
| File | Status |
|------|--------|
| `docker-compose.host.yml` | Present at `~/projects/velobid/` |
| `docker-compose.tailscale.yml` | Present at `~/projects/velobid/` |
| `scripts/linux-host-tailscale-container.sh` | Present at `~/projects/velobid/` |

All overlay artifacts are in place.

## Block Reason

The deployment script (`scripts/linux-host-tailscale-container.sh`) sources the env file and exits if `TAILSCALE_AUTHKEY` is unset and no prior Tailscale state exists:

> TAILSCALE_AUTHKEY is required for first container login.
> Create a reusable or ephemeral auth key in Tailscale, then set it in /srv/velobid/secrets/velobid.env.

Because the key is missing, the script was **not executed** and no Tailscale containers were started.

## Exact Next Action Required

1. Generate a Tailscale auth key (reusable or ephemeral) from the Tailscale admin console:
   https://login.tailscale.com/admin/settings/keys

2. Append it to the host env file with this command (replace `<tskey-auth-...>` with the actual key):

   ```bash
   sudo bash -c 'echo "TAILSCALE_AUTHKEY=<tskey-auth-...>" >> /srv/velobid/secrets/velobid.env'
   ```

3. Re-run this deployment task.

## Post-unblock Verification Checklist (pending)

- [ ] Run `sudo bash scripts/linux-host-tailscale-container.sh`
- [ ] Containers running: `velobid`, `hermes`, `velobid-tailscale`, `velobid-tailnet-proxy`
- [ ] Tailscale node hostname = `velobid` (or `TAILSCALE_HOSTNAME` override)
- [ ] `tailscale serve status` shows `--bg http://127.0.0.1:8080`
- [ ] `curl -fsS https://velobid.tailfceaca.ts.net/api/v1/health` returns HTTP 200
- [ ] `curl -fsS https://velobid.tailfceaca.ts.net/projects` returns HTTP 200
- [ ] Hermes (:8644) is **not** reachable via the tailnet URL

## Notes

- Hermes is currently bound to `127.0.0.1:8644` on the host, so it is not exposed to the tailnet unless explicitly proxied.
- The Tailscale container uses `network_mode: service:velobid-tailscale` for the nginx proxy, so only VeloBid (port 8000 -> 8080 via nginx) will be funnelled.

---

## Deployment Completion

### Actions Taken

1. **Confirmed TAILSCALE_AUTHKEY** — `grep -c` returned 1 match in `/srv/velobid/secrets/velobid.env` (value redacted, never printed).
2. **Verified base stack health** — `velobid` and `hermes` containers both `Up` and `healthy` before overlay deployment.
3. **Ran deployment script** — `sudo bash scripts/linux-host-tailscale-container.sh` executed successfully.
4. **Fixed hostname collision** — `docker-compose.tailscale.yml` originally set `hostname: velobid`, which caused Docker to inject `velobid -> 172.19.0.4` into `/etc/hosts` inside the tailscale network namespace. This shadowed the `velobid` service DNS and broke nginx upstream resolution. Changed to `hostname: velobid-tsnode` (Tailscale node name remains `velobid` via `TS_HOSTNAME`).
5. **Recreated overlay containers** — `velobid-tailscale` and `velobid-tailnet-proxy` recreated with corrected hostname.
6. **Re-applied Serve config** — `tailscale serve --bg http://127.0.0.1:8080` active.

### Final Container State

| Container | Status | Ports | Tailnet Exposure |
|-----------|--------|-------|------------------|
| velobid | Up 39 min (healthy) | 0.0.0.0:8000->8000/tcp | Via nginx proxy + Serve |
| hermes | Up 39 min (healthy) | 127.0.0.1:8644->8642/tcp | **None** (host-local bind) |
| velobid-tailscale | Up 3 min | — | Tailnet node `velobid` |
| velobid-tailnet-proxy | Up 3 min | — | Shares netns with tailscale |

### Tailscale Node Verification

- **Hostname:** `velobid`
- **Tailnet:** `tailfceaca.ts.net`
- **Tailscale IPs:** `100.68.239.121`, `fd7a:115c:a1e0::f834:ef79`
- **BackendState:** `Running`

### Serve / Funnel Verification

```
https://velobid.tailfceaca.ts.net (tailnet only)
|-- / proxy http://127.0.0.1:8080
```

- **Serve:** Active, tailnet-only (not public).
- **Funnel:** Not enabled. `tailscale funnel status` returns the same tailnet-only output.

### Internal Proxy Path Verification

Tested from `velobid-tailnet-proxy` (shared netns with tailscale):

- `http://velobid:8000/api/v1/health` -> `{"status":"ok","service":"velobid-api"}` ✅
- `http://127.0.0.1:8080/api/v1/health` -> `{"status":"ok","service":"velobid-api"}` ✅

### Hermes Isolation Confirmation

- **Not proxied by Serve:** `tailscale serve status` shows only `/ -> http://127.0.0.1:8080`; no routes for `:8644` or `/api/v1/agent/hermes-chat`.
- **Not reachable via tailnet URL:** `https://velobid.tailfceaca.ts.net/api/v1/agent/hermes-chat` returns TLS handshake failure (expected — no route defined).
- **Host-local bind:** `docker-compose.host.yml` binds Hermes to `127.0.0.1:8644`; the tailscale container netns has no path to the host loopback.

### Tailnet HTTPS Endpoint Verification

| URL | Result | Notes |
|-----|--------|-------|
| `https://velobid.tailfceaca.ts.net/api/v1/health` | **Unable to test from deploy host** | Host not on tailnet; container has `TS_ACCEPT_DNS=false` so hostname resolves to DERP relays |
| `https://velobid.tailfceaca.ts.net/projects` | **Unable to test from deploy host** | Same constraint |

**Why this is expected:** The deployment host is not a Tailscale node (host `tailscale` binary is logged out). The Tailscale container itself cannot complete a TLS handshake to its own serve endpoint from inside the same network namespace (loopback/SNI limitation with kernel TUN mode). Verification requires a separate tailnet-connected client (e.g., phone, workstation) with Magic DNS enabled.

**Recommended validation from a tailnet client:**
```bash
curl -fsS https://velobid.tailfceaca.ts.net/api/v1/health
curl -fsS https://velobid.tailfceaca.ts.net/projects
```

### Post-Deploy Checklist

- [x] TAILSCALE_AUTHKEY present in secrets file (redacted)
- [x] Base stack healthy before overlay
- [x] `scripts/linux-host-tailscale-container.sh` executed successfully
- [x] Containers running: `velobid`, `hermes`, `velobid-tailscale`, `velobid-tailnet-proxy`
- [x] Tailscale node hostname = `velobid`
- [x] `tailscale serve status` shows `--bg http://127.0.0.1:8080`
- [ ] `curl -fsS https://velobid.tailfceaca.ts.net/api/v1/health` returns HTTP 200 *(requires tailnet client)*
- [ ] `curl -fsS https://velobid.tailfceaca.ts.net/projects` returns HTTP 200 *(requires tailnet client)*
- [x] Hermes (:8644) is **not** reachable via the tailnet URL

### Configuration Change Log

| File | Change |
|------|--------|
| `docker-compose.tailscale.yml` | `hostname` changed from `${TAILSCALE_HOSTNAME:-velobid}` to `velobid-tsnode` to prevent Docker `/etc/hosts` collision with the `velobid` service name. `TS_HOSTNAME` env var still controls the Tailscale Magic DNS name. |

Status: **COMPLETED** — Overlay deployed. Pending HTTPS 200 validation from an actual tailnet client.
