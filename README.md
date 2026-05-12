# VeloBid

VeloBid is a Dockerized bid generation and Hermes-assisted estimating stack.

## License and Usage

VeloBid is provided under the [VeloBid Personal Use and Non-Commercial
License v1.0](LICENSE). Personal and non-commercial use (evaluation,
education, personal projects) is free. **Commercial use requires a separate
written commercial license.** See [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md)
for details and licensing inquiries.

## Current Paths

VeloBid now has two container paths:

- **Dev sync:** mounted source + Vite HMR for fast local iteration
- **Production:** Linux host Docker directly, deployed from a commit

Production uses:

- VeloBid API/UI container
- Hermes gateway container
- persistent host storage under `/srv/velobid`
- backup and restore scripts under `scripts/`

Start here:

- [Documentation index](docs/README.md)
- [Container sync notes](docs/container-sync-notes.md)
- [Development workflow](docs/development.md)
- [Testing guide](docs/testing.md)
- [Linux host runbook](docs/runbook-linux-no-vm.md)
- [Documentation status](docs/DOCUMENTATION_STATUS.md)
- [Latest run report (2026-05-08)](docs/kaban-opencode-run-report-2026-05-08.md)

## Common Commands

```bash
docker compose -f docker-compose.dev.yml up --build
sudo bash scripts/linux-host-init.sh
sudo bash scripts/linux-host-deploy.sh
sudo bash scripts/linux-host-backup.sh
python scripts/verify.py
python scripts/verify.py --live
```

## Notes

The older libvirt/KVM VM bootstrap path is archived under `docs/archive/` for reference. It is not the current deployment path.
