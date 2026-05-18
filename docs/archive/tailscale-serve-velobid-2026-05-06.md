> **ARCHIVED** — Historical Tailscale Serve configuration report from 2026-05-06. Tailscale Funnel/Serve config was completed and is operational; no further configuration changes expected.
> This document has been archived because its purpose has been fulfilled or superseded by newer documentation.
> See  for the current development plan.
> Original location: 
# Tailscale Serve Configuration Report — VeloBid
Date: 2026-05-06

## Objective
Configure Tailscale Serve (tailnet-only) for the active no-VM VeloBid Docker deployment on the Linux host, routing `https://velobid.tailfceaca.ts.net/projects` to `http://127.0.0.1:8000/projects`. Use Serve, not Funnel. Do not expose Hermes.

---

## Initial State
| Item | Value |
|------|-------|
| Tailscale version | 1.96.4 |
| Hostname (before) | `selfsim-machine` |
| DNS name (before) | `selfsim-machine.tailfceaca.ts.net` |
| Funnel active? | Yes — `https://velobid.tailfceaca.ts.net` → `http://127.0.0.1:8000` |
| Hermes exposed? | Yes — `https://selfsim-machine.tailfceaca.ts.net:9119` (tailnet only) |

---

## Steps Executed

### 1. Inspect status & conflicts
```
tailscale status --json
tailscale serve status --json
tailscale funnel status
```

**Finding:** The tailnet contains an *offline* machine named `velobid` (100.77.7.29, last seen 3h ago) still holding the `velobid.tailfceaca.ts.net` DNS record. The current live host was `selfsim-machine`.

### 2. Rename host
```
sudo tailscale set --hostname=velobid
```
Result: hostname updated, but Tailscale appended `-1` because `velobid` is already taken by the offline node.
- **New hostname:** `velobid-1`
- **New DNS name:** `velobid-1.tailfceaca.ts.net`

### 3. Clear stale configs
```
sudo tailscale funnel reset
sudo tailscale serve reset
```
Both Funnel and Serve configs were removed. Hermes is no longer exposed via Serve.

### 4. Configure Tailscale Serve
```
sudo tailscale serve --bg http://127.0.0.1:8000
```

**Result:**
```
https://velobid-1.tailfceaca.ts.net/
|-- proxy http://127.0.0.1:8000
Serve started and running in the background.
```

---

## Verification

### Local API health check
```
curl -sL http://127.0.0.1:8000/api/v1/health
```
Response: `{"status":"ok","service":"velobid-api"}` — HTTP 200

### Tailscale HTTPS health check
```
curl -sL https://velobid-1.tailfceaca.ts.net/api/v1/health
```
Response: `{"status":"ok","service":"velobid-api"}` — HTTP 200

### Tailscale HTTPS SPA route
```
curl -sL https://velobid-1.tailfceaca.ts.net/projects
```
Response: VeloBid `index.html` — HTTP 200

### Hermes exposure check
```
tailscale serve status
```
Result: No Hermes handlers configured. Hermes is **not** exposed via Serve or Funnel.

---

## Current State
| Item | Value |
|------|-------|
| Tailscale hostname | `velobid-1` |
| Tailscale DNS name | `velobid-1.tailfceaca.ts.net` |
| Serve target | `https://velobid-1.tailfceaca.ts.net/` → `http://127.0.0.1:8000` |
| Funnel active? | **No** |
| Hermes exposed? | **No** |
| VeloBid reachable on tailnet? | **Yes** |

---

## Blocker: `velobid` Hostname
The target URL `https://velobid.tailfceaca.ts.net` is **not yet available** because another tailnet node (`velobid`, 100.77.7.29) is offline but still registered and holds the DNS name.

### Required Admin Action
1. Open the Tailscale admin console: https://login.tailscale.com/admin/machines
2. Find the offline machine named **velobid** (100.77.7.29)
3. Remove / expire the device
4. On this host, run:
   ```bash
   sudo tailscale set --hostname=velobid
   sudo tailscale serve --bg http://127.0.0.1:8000
   ```

After the old node is removed and the rename completes, `https://velobid.tailfceaca.ts.net/projects` will route to the VeloBid app as requested.

---

## Commands Summary
```bash
# Inspect
tailscale status
tailscale serve status
tailscale funnel status

# Rename (blocked until old velobid removed)
sudo tailscale set --hostname=velobid

# Reset and re-apply Serve
sudo tailscale funnel reset
sudo tailscale serve reset
sudo tailscale serve --bg http://127.0.0.1:8000

# Disable Serve if needed later
sudo tailscale serve --https=443 off
```

---

## Retry — 2026-05-07

### Check: Is the old offline `velobid` node gone?
```
tailscale status --json
```
**Result:** The old offline node `velobid` (100.77.7.29) is **no longer present** in the peer list. Only `velobid-1` (this host, 100.96.70.102), `pixel-8-pro`, and `WIN-RPN6F5DAP5K` remain.

### Hostname rename attempted
```
sudo tailscale set --hostname=velobid
```
Result: command returned exit code 0.
- Local prefs now show `"Hostname": "velobid"`.
- DNS name still resolves as `velobid-1.tailfceaca.ts.net` because the node cannot sync with the control plane.

### Blocker: Node requires re-authentication
After the hostname change and a `tailscaled` restart, the daemon entered `NeedsLogin` state:
```
Switching ipn state NoState -> NeedsLogin (WantRunning=true, nm=false)
```
Pre-restart logs showed repeated:
```
PollNetMap: initial fetch failed 404: node not found
```
This indicates the node identity (`n7qdDwoXpB21CNTRL`) was removed or expired in the Tailscale admin console.

### Serve / Funnel / Hermes status
- `tailscale serve status --json` returns `{}` (no active handlers).
- `tailscale funnel status` returns `{}` (no public exposure).
- **Hermes is not exposed** via Serve or Funnel.
- The local VeloBid API remains healthy at `http://127.0.0.1:8000/api/v1/health` → HTTP 200.

### Next command
Run to re-authenticate the node:
```bash
sudo tailscale up --force-reauth
```
After authenticating, re-run:
```bash
sudo tailscale set --hostname=velobid
sudo tailscale serve --bg http://127.0.0.1:8000
```
Then verify:
```bash
curl -sL https://velobid.tailfceaca.ts.net/api/v1/health
curl -sL https://velobid.tailfceaca.ts.net/projects
```