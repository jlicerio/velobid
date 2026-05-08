# VeloBid Linux Host Runbook (No VM)

> **ACTIVE — Primary deployment runbook**
> This is the current Phase 1 deployment path: run VeloBid and Hermes directly on a Linux host with Docker Compose, persistent host storage at `/srv/velobid`, and the `scripts/linux-host-*.sh` toolkit.
> The older VM-based path (libvirt/KVM) is archived under `docs/archive/` for reference.

This is the simpler Phase 1 deployment path: run VeloBid and Hermes directly on a Linux host with Docker Compose, persistent host storage, and backup routes.

## When to use this
- You want to avoid libvirt/KVM VM rebuilds.
- You have one Linux server that can run Docker.
- You want an inexpensive beta setup that can later move to a second server, managed storage, or cloud.

## Architecture

Services:
- `velobid`: FastAPI app + built frontend on port `8000`
- `hermes`: Hermes gateway on port `8644`, bound to localhost by default

Persistent storage:
- `/srv/velobid/config`: live project/trade/bidder config
- `/srv/velobid/bid_projects`: legacy project workspace
- `/srv/velobid/data`: generated bids, files, blueprints, shared runtime data
- `/srv/velobid/hermes`: Hermes state and profiles
- `/srv/velobid/backups`: local encrypted-host backup route target
- `/srv/velobid/secrets/velobid.env`: runtime environment file

## 1) Install Docker on Linux host

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"
sudo docker version
sudo docker compose version
```

## 2) Initialize host storage

From the repo:

```bash
cd /home/selfsim/projects/velobid
sudo bash scripts/linux-host-init.sh
```

Then edit:

```bash
sudo nano /srv/velobid/secrets/velobid.env
```

Required edits:
- Set `HERMES_API_KEY` to a real internal token.
- Set `HERMES_CREDENTIALS_JSON` if Hermes needs external model credentials.
- Set `VELOBID_BIND_ADDR=127.0.0.1` if putting Caddy/Nginx in front.

## 3) Deploy or update

```bash
cd /home/selfsim/projects/velobid
sudo bash scripts/linux-host-deploy.sh
```

The deploy script:
- builds both images
- starts `velobid` and `hermes`
- waits for API health
- waits for Hermes gateway health

Manual equivalent:

```bash
sudo docker compose --env-file /srv/velobid/secrets/velobid.env -f docker-compose.host.yml up -d --build
sudo docker compose --env-file /srv/velobid/secrets/velobid.env -f docker-compose.host.yml ps
```

## 4) Health checks

```bash
curl -fsS http://127.0.0.1:8000/api/v1/meta
curl -fsS http://127.0.0.1:8000/api/v1/health
curl -fsS -H "Authorization: Bearer $(grep '^HERMES_API_KEY=' /srv/velobid/secrets/velobid.env | cut -d= -f2-)" \
  http://127.0.0.1:8644/v1/models
```

Pass gate:
- `velobid` returns `200` for meta and health.
- `hermes` returns a model list.
- `docker compose ps` shows both services healthy.

## 5) Backups

Local backup:

```bash
sudo bash scripts/linux-host-backup.sh
```

This creates:

```text
/srv/velobid/backups/velobid-<timestamp>.tar.gz
/srv/velobid/backups/velobid-<timestamp>.tar.gz.sha256
```

Cron example:

```bash
sudo crontab -e
```

Add:

```cron
17 */6 * * * cd /home/selfsim/projects/velobid && bash scripts/linux-host-backup.sh >> /var/log/velobid-backup.log 2>&1
```

Optional offsite route:
- Install `restic`.
- Set `RESTIC_REPOSITORY`, `RESTIC_PASSWORD`, and provider credentials in `/srv/velobid/secrets/velobid.env`.
- Run `sudo bash scripts/linux-host-backup.sh` again.

Good low-cost offsite targets:
- Backblaze B2
- Wasabi
- S3-compatible NAS/MinIO
- second self-hosted server over SFTP with restic

## 6) Restore

Preview restore:

```bash
sudo bash scripts/linux-host-restore.sh /srv/velobid/backups/<backup-file>.tar.gz
```

Apply restore:

```bash
cd /home/selfsim/projects/velobid
sudo docker compose --env-file /srv/velobid/secrets/velobid.env -f docker-compose.host.yml down
sudo bash scripts/linux-host-restore.sh /srv/velobid/backups/<backup-file>.tar.gz --apply
sudo bash scripts/linux-host-deploy.sh
```

Pass gate:
- Restore preview extracts cleanly.
- Applied restore passes health checks.
- Project list and generated files are visible.

## 7) Normal app updates

```bash
cd /home/selfsim/projects/velobid
git pull
sudo bash scripts/linux-host-deploy.sh
```

No VM rebuild is needed for normal API/UI changes.

## 8) Public access

For private beta operations:
- Keep admin access through Tailscale.
- Keep `HERMES_BIND_ADDR=127.0.0.1`.

For public users:
- Put Caddy or Nginx in front of VeloBid.
- Set `VELOBID_BIND_ADDR=127.0.0.1`.
- Open only ports `80` and `443` publicly.

Example Caddy route:

```caddyfile
velobid.example.com {
  reverse_proxy 127.0.0.1:8000
}
```

## 9) Optional: dedicated Tailscale container for VeloBid

Use this when VeloBid should have its own tailnet node, separate from the Linux host identity.

This follows Tailscale's Docker pattern:
- `velobid-tailscale`: Tailscale client container with persistent state
- `velobid-tailnet-proxy`: nginx proxy sharing the Tailscale container network namespace
- Tailscale Serve: HTTPS tailnet URL to the proxy, then to `velobid:8000`

First, generate a Tailscale auth key from the admin console and edit:

```bash
sudo nano /srv/velobid/secrets/velobid.env
```

Set:

```env
TAILSCALE_HOSTNAME=velobid
TAILSCALE_TAILNET=tailfceaca.ts.net
TAILSCALE_STATE_DIR=/srv/velobid/tailscale
TAILSCALE_AUTHKEY=<tskey-auth-redacted>
```

Start the containerized Tailscale route:

```bash
cd /home/selfsim/projects/velobid
sudo bash scripts/linux-host-tailscale-container.sh
```

Verify from a tailnet client:

```bash
curl -fsS https://velobid.tailfceaca.ts.net/api/v1/health
open https://velobid.tailfceaca.ts.net/projects
```

Notes:
- The Tailscale state is stored in `/srv/velobid/tailscale`.
- Backups include this state, so protect backup archives like secrets.
- Hermes is still not exposed by this overlay.

## 10) Two-server upgrade path

Server A:
- Runs VeloBid and Hermes.
- Accepts public HTTPS traffic.

Server B:
- Receives restic backups.
- Optionally keeps a warm clone of the repo and Docker images.

Manual failover:
- Restore latest backup on Server B.
- Run `sudo bash scripts/linux-host-deploy.sh`.
- Move DNS or reverse proxy target to Server B.

This keeps Phase 1 cheap while giving you a clean path to Phase 2.
