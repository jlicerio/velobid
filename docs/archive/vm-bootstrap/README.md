# VeloBid — Phase 1 VM Bootstrap Pack

> **ARCHIVED — 2026-05-06**
> This directory contains the cloud-init artifacts and scripts for provisioning a VM under libvirt + qemu + KVM.
> The VM path is no longer the active deployment strategy. The current path is Linux host Docker directly — see `docs/runbook-linux-no-vm.md`.
> These files are kept for reference and disaster-recovery scenarios.

This directory contains the cloud-init artifacts and scripts needed to
provision a production-safe Ubuntu 24.04 LTS virtual machine for running
VeloBid under libvirt + qemu + KVM.

**Host prerequisites** (the machine that runs the VM):

- Ubuntu 22.04 or 24.04 host
- `libvirt-daemon-system`, `libvirt-clients`, `virtinst`, `cloud-image-utils`, `qemu-utils`, `wget`

---

## File Overview

| File | Purpose | Runs on |
|------|---------|---------|
| `user-data.hardened.yaml` | Cloud-init user-data: packages, services, SSH hardening | VM (at first boot) |
| `meta-data.yaml` | Cloud-init metadata: instance-id, hostname | VM (at first boot) |
| `network-config.yaml` | Cloud-init network config: DHCP on virtio NIC | VM (at first boot) |
| `host-runbook.sh` | Full VM lifecycle: reset network, create disk, launch | **Host** (sudo) |
| `verify-phase1.sh` | Post-boot verification: all services, PASS/FAIL gates | **VM** (or via SSH) |

---

## Execution Order

### Step 1 — Insert your SSH public key

Edit `user-data.hardened.yaml` and find the `users:` section.
Uncomment the `ssh_authorized_keys:` block and replace the placeholder
with **your public key** (the content of `~/.ssh/id_ed25519.pub` or equivalent):

```yaml
users:
  - name: ubuntu
    ssh_authorized_keys:
      - "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI... your-email@example.com"
    # ... remaining fields unchanged
```

> **Without a public key in this file you will not be able to SSH into the VM.**
> The VM has password authentication disabled and root login is locked to
> key-only from the start.

### Step 2 — Run the host runbook

```bash
sudo bash docs/archive/vm-bootstrap/host-runbook.sh
```

This script:

1. Checks that all required tools (virsh, virt-install, cloud-localds, etc.)
   are installed.
2. Destroys any existing VM with the same name (`velobid` by default).
3. Resets the **libvirt default network** (stop → undefine → re-define → start).
4. Downloads the Ubuntu 24.04 LTS cloud image if not already cached.
5. Creates a copy-on-write (COW) qcow2 disk backed by the cloud image.
6. Generates a cloud-init seed ISO from the three YAML files.
7. Launches the VM with `virt-install` (serial console, no graphical window).
8. Prints connection instructions.

**Environment variables** (all optional):

| Variable | Default | Purpose |
|----------|---------|---------|
| `VM_NAME` | `velobid` | libvirt domain name |
| `VM_RAM_MB` | `4096` | Memory in MB |
| `VM_VCPUS` | `4` | Number of vCPUs |
| `VM_DISK_GB` | `30` | Root disk size in GB |
| `VM_BRIDGE` | `default` | libvirt network name |
| `IMAGE_DIR` | `/var/lib/libvirt/images` | Image storage directory |
| `BOOTSTRAP_DIR` | *(script's directory)* | Where the YAML files live |

Example with overrides:

```bash
sudo VM_NAME=velobid-prod VM_RAM_MB=8192 VM_DISK_GB=50 bash docs/archive/vm-bootstrap/host-runbook.sh
```

### Step 3 — Wait for boot + find the IP

The VM takes 30–90 seconds to boot on first start. Find its IP address:

```bash
sudo virsh net-dhcp-leases default
```

Alternatively, attach to the serial console:

```bash
sudo virsh console velobid
```

(Exit the console with **Ctrl+]**.)

### Step 4 — Verify Phase 1

Copy `verify-phase1.sh` to the VM (or run via SSH) to confirm everything
is healthy:

```bash
ssh ubuntu@<VM-IP> 'bash -s' < docs/archive/vm-bootstrap/verify-phase1.sh
```

All checks must print **PASS**. If any check fails, the script exits with
code 1 — investigate the failing service before proceeding.

### Step 5 — Authenticate Tailscale (manual)

No auth key is embedded anywhere. Inside the VM:

```bash
sudo tailscale up --ssh
```

Follow the browser URL to authenticate. Once connected, the VM will be
reachable on your tailnet even if the IP changes.

### Step 6 — Deploy VeloBid

Follow the project's deployment instructions (e.g., `docker compose up -d`
or the K8s manifests under `k8s/`).

---

## Security Notes

- **No secrets in version control.** The cloud-init user-data file contains
  no API keys, no Tailscale auth keys, and no passwords. The SSH public key
  must be added locally before use.
- **SSH is hardened immediately at first boot:** password auth is disabled,
  root login is locked to key-only.
- **UFW defaults:** deny incoming, allow outgoing, allow SSH (port 22).
- **fail2ban** is installed and enabled to rate-limit SSH attempts.
- **Docker CE** is installed from the official Docker repository (not Ubuntu's
  snap or apt archive).

---

## Troubleshooting

| Symptom | Likely cause |
|---------|-------------|
| `virt-install: command not found` | `virtinst` package missing: `sudo apt-get install virtinst` |
| `cloud-localds: command not found` | `cloud-image-utils` package missing: `sudo apt-get install cloud-image-utils` |
| VM boots but SSH connection refused | No SSH key in `user-data.hardened.yaml`; attach via `virsh console` and debug |
| `virsh` fails with permission denied | Run runbook with `sudo` |
| `virsh net-define default.xml` fails | `libvirt-daemon-system` not installed or libvirtd not running: `sudo systemctl enable --now libvirtd` |
| VM has no IP after boot | Check `network-config.yaml` matches the NIC model (default: virtio). If using a different NIC model, update the `match:` rule. |

---

## What Phase 1 Does NOT Do

- Does **not** authenticate Tailscale (manual step)
- Does **not** deploy VeloBid (that's Phase 2+)
- Does **not** set up monitoring, log shipping, or backups
- Does **not** configure Docker Swarm or K8s
- Does **not** apply CIS-level kernel hardening
