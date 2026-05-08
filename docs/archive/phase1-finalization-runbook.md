# VeloBid Phase 1 Finalization Runbook

> **ARCHIVED — 2026-05-06**
> This runbook describes the VM-based Phase 1 deployment path (libvirt/KVM).
> It has been superseded by the Linux host Docker path. See `docs/runbook-linux-no-vm.md` for the current active runbook.

Goal: finish Phase 1 with a stable single-node VM deployment (Docker Compose), verified networking/SSH, and reproducible health checks.

## Exit Criteria (Phase 1 is done when all are true)
- [ ] VM boots reliably and keeps stable network lease.
- [ ] SSH access is stable for 30+ minutes without reconnect failures.
- [ ] Tailscale connectivity works to the VM.
- [ ] `docker compose up -d --build` succeeds on VM.
- [ ] VeloBid and Hermes are healthy.
- [ ] Core endpoints pass smoke tests.
- [ ] Recovery notes are documented in repo docs.

## 1) Host-side libvirt network reset

```bash
set -euo pipefail

sudo virsh net-destroy default || true
sudo virsh net-undefine default || true

cat <<'EOF' | sudo tee /tmp/default-net.xml >/dev/null
<network>
  <name>default</name>
  <forward mode='nat'/>
  <bridge name='virbr0' stp='on' delay='0'/>
  <ip address='192.168.122.1' netmask='255.255.255.0'>
    <dhcp>
      <range start='192.168.122.100' end='192.168.122.254'/>
    </dhcp>
  </ip>
</network>
EOF

sudo virsh net-define /tmp/default-net.xml
sudo virsh net-autostart default
sudo virsh net-start default

virsh net-list --all
virsh net-dhcp-leases default || true
ip a show virbr0
```

Pass gate:
- [ ] `default` network is active/autostart.
- [ ] `virbr0` exists with `192.168.122.1/24`.

## 2) Rebuild VM with corrected cloud-init

Use cloud-init with:
- unique `instance-id`
- `systemctl restart ssh` (not `sshd`)
- no plaintext secrets in `user-data` when possible

Minimal `meta-data`:
```yaml
instance-id: velobid-001
local-hostname: velobid
```

Recreate VM:
```bash
sudo virsh destroy velobid || true
sudo virsh undefine velobid --nvram || true
sudo rm -f /var/lib/libvirt/images/velobid-vm.qcow2 /var/lib/libvirt/images/velobid-seed.qcow2

cloud-localds -v ~/vm-images/velobid-seed.qcow2 \
  ~/vm-images/cloud-init/user-data \
  ~/vm-images/cloud-init/meta-data

sudo mv ~/vm-images/velobid-seed.qcow2 /var/lib/libvirt/images/
sudo chown libvirt-qemu:kvm /var/lib/libvirt/images/velobid-seed.qcow2
sudo chmod 644 /var/lib/libvirt/images/velobid-seed.qcow2

sudo qemu-img create -f qcow2 \
  -b /var/lib/libvirt/images/debian-12-genericcloud-amd64.qcow2 -F qcow2 \
  /var/lib/libvirt/images/velobid-vm.qcow2 30G
sudo chown libvirt-qemu:kvm /var/lib/libvirt/images/velobid-vm.qcow2

sudo virt-install \
  --name=velobid \
  --vcpus=4 \
  --memory=8192 \
  --disk path=/var/lib/libvirt/images/velobid-vm.qcow2,format=qcow2,bus=virtio \
  --disk path=/var/lib/libvirt/images/velobid-seed.qcow2,device=cdrom \
  --os-variant=debian12 \
  --network network=default,model=virtio \
  --graphics none \
  --console pty,target_type=serial \
  --noautoconsole \
  --import
```

Pass gate:
- [ ] VM starts without crash loop.
- [ ] DHCP lease appears and remains stable.

## 3) Verify boot path and SSH stability

```bash
virsh domifaddr velobid
virsh net-dhcp-leases default

VM_IP="<set-vm-ip>"
ssh -o StrictHostKeyChecking=accept-new debian@"$VM_IP" 'hostnamectl; cloud-init status --wait'
ssh debian@"$VM_IP" 'ip a; ip r; systemctl is-active ssh; docker --version'
```

30-minute stability check:
```bash
for i in $(seq 1 30); do
  ssh -o ConnectTimeout=5 debian@"$VM_IP" 'echo ok' || exit 1
  sleep 60
done
echo "SSH stability check passed"
```

Pass gate:
- [ ] All 30 checks pass.

## 4) Join Tailscale on VM and verify reachability

On VM:
```bash
sudo tailscale up --hostname=velobid
tailscale ip -4
tailscale status
```

From host:
```bash
ping -c 3 <vm_tailscale_ip>
ssh debian@<vm_tailscale_ip> 'echo tailscale-ssh-ok'
```

Pass gate:
- [ ] VM is visible in `tailscale status`.
- [ ] SSH works over Tailscale path.

## 5) Deploy VeloBid/Hermes compose stack on VM

```bash
rsync -avz --delete ~/projects/velobid/ debian@"$VM_IP":/opt/velobid/
ssh debian@"$VM_IP" 'cd /opt/velobid && docker compose down -v || true'
ssh debian@"$VM_IP" 'cd /opt/velobid && docker compose up -d --build'
ssh debian@"$VM_IP" 'cd /opt/velobid && docker compose ps'
```

Pass gate:
- [ ] `velobid` and `hermes` are `Up` and healthy.

## 6) Health + smoke checks

```bash
curl -fsS http://"$VM_IP":8000/api/v1/meta
curl -fsS http://"$VM_IP":8000/api/v1/health
curl -fsS http://"$VM_IP":8644/v1/models
```

Optional extended smoke:
```bash
ssh debian@"$VM_IP" 'cd /opt/velobid && make test'
```

Pass gate:
- [ ] API endpoints return expected responses.
- [ ] Hermes models endpoint returns 200.

## 7) Capture evidence and close Phase 1

Collect:
```bash
ssh debian@"$VM_IP" 'cd /opt/velobid && docker compose ps'
ssh debian@"$VM_IP" 'cd /opt/velobid && docker compose logs --tail=100 velobid hermes'
```

Update docs:
- `/home/selfsim/velobid-tailscale-migration-log.md`
- `docs/archive/hermes-docker-full-run-2026-05-06.md`

Final signoff:
- [ ] Networking stable
- [ ] SSH stable
- [ ] Tailscale stable
- [ ] Compose stable
- [ ] Health checks green
- [ ] Evidence documented

If all checked, Phase 1 is complete.
