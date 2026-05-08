# VeloBid

VeloBid is a Dockerized bid generation and Hermes-assisted estimating stack.

## Current Phase 1 Path

The active deployment path is **Linux host Docker directly**:

- VeloBid API/UI container
- Hermes gateway container
- persistent host storage under `/srv/velobid`
- backup and restore scripts under `scripts/`

Start here:

- [Documentation index](docs/README.md)
- [Linux host runbook](docs/runbook-linux-no-vm.md)
- [Documentation status](docs/DOCUMENTATION_STATUS.md)
- [Latest run report (2026-05-08)](docs/kaban-opencode-run-report-2026-05-08.md)

## Common Commands

```bash
sudo bash scripts/linux-host-init.sh
sudo bash scripts/linux-host-deploy.sh
sudo bash scripts/linux-host-backup.sh
```

## Notes

The older libvirt/KVM VM bootstrap path is archived under `docs/archive/` for reference. It is not the current deployment path.
