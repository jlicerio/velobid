#!/usr/bin/env bash
# =============================================================================
# VeloBid — Phase 1 VM Bootstrap: host-runbook.sh
# Purpose:  Run on the LIBVIRT HOST to destroy and recreate the Phase 1 VM.
# Usage:    sudo bash host-runbook.sh
#
# This script:
#   1. Checks prerequisites (virsh, virt-install, cloud-localds, qemu-img).
#   2. Resets the libvirt default network (stop → undefine → define → start).
#   3. Downloads the Ubuntu 24.04 LTS cloud image if missing.
#   4. Creates a COW (copy-on-write) disk from the cloud image.
#   5. Generates the cloud-init ISO from user-data + meta-data + network-config.
#   6. Launches the VM with virt-install (serial console, no graphics).
#   7. Prints connection instructions.
#
# Environment variables (all optional):
#   VM_NAME        — name of the libvirt domain  (default: velobid)
#   VM_RAM_MB      — memory in MB               (default: 4096)
#   VM_VCPUS       — number of vCPUs             (default: 4)
#   VM_DISK_GB     — root disk size in GB        (default: 30)
#   VM_BRIDGE      — libvirt network name        (default: default)
#   IMAGE_DIR      — directory for images        (default: /var/lib/libvirt/images)
#   CLOUD_IMAGE    — Ubuntu cloud image path     (default: auto-detect 24.04)
#   BOOTSTRAP_DIR  — where .yaml files live      (default: script directory)
# =============================================================================

set -euo pipefail

# ---- Configuration (overridable via env) ----
VM_NAME="${VM_NAME:-velobid}"
VM_RAM_MB="${VM_RAM_MB:-4096}"
VM_VCPUS="${VM_VCPUS:-4}"
VM_DISK_GB="${VM_DISK_GB:-30}"
VM_BRIDGE="${VM_BRIDGE:-default}"
IMAGE_DIR="${IMAGE_DIR:-/var/lib/libvirt/images}"
BOOTSTRAP_DIR="${BOOTSTRAP_DIR:-$(cd "$(dirname "$0")" && pwd)}"

# ---- Ubuntu cloud image settings ----
CLOUD_IMAGE_URL="${CLOUD_IMAGE_URL:-https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img}"
CLOUD_IMAGE_NAME="${CLOUD_IMAGE_NAME:-noble-server-cloudimg-amd64.img}"

# ---- Derived paths ----
CLOUD_IMAGE_PATH="${IMAGE_DIR}/${CLOUD_IMAGE_NAME}"
VM_DISK_PATH="${IMAGE_DIR}/${VM_NAME}.qcow2"
SEED_ISO_PATH="${IMAGE_DIR}/${VM_NAME}-seed.iso"
USER_DATA="${BOOTSTRAP_DIR}/user-data.hardened.yaml"
META_DATA="${BOOTSTRAP_DIR}/meta-data.yaml"
NETWORK_CONFIG="${BOOTSTRAP_DIR}/network-config.yaml"

# ---- Colors ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass() { echo -e "  ${GREEN}[PASS]${NC} $1"; }
fail() { echo -e "  ${RED}[FAIL]${NC} $1"; exit 1; }
info() { echo -e "  ${YELLOW}[INFO]${NC} $1"; }

# =============================================================================
echo "=============================================="
echo " VeloBid Phase 1 — Host VM Runbook"
echo "=============================================="
echo ""

# ---- Pre-flight checks ----
echo "--- Prerequisites ---"
for cmd in virsh virt-install cloud-localds qemu-img wget; do
  command -v "$cmd" >/dev/null 2>&1 || fail "'$cmd' not found. Install it:\n  sudo apt-get install -y libvirt-daemon-system libvirt-clients virtinst cloud-image-utils wget"
  pass "$cmd found"
done

[ -d "$IMAGE_DIR" ] || fail "Image directory $IMAGE_DIR does not exist. Create it:\n  sudo mkdir -p $IMAGE_DIR"
pass "Image directory $IMAGE_DIR exists"

[ -f "$USER_DATA" ]   || fail "Missing $USER_DATA"
[ -f "$META_DATA" ]   || fail "Missing $META_DATA"
[ -f "$NETWORK_CONFIG" ] || fail "Missing $NETWORK_CONFIG"
pass "Bootstrap YAML files found"

# ---- Stop & destroy existing VM ----
echo ""
echo "--- Cleaning up existing VM (if any) ---"
if virsh dominfo "$VM_NAME" >/dev/null 2>&1; then
  info "Destroying existing domain '$VM_NAME'..."
  virsh destroy "$VM_NAME" 2>/dev/null || true
  virsh undefine "$VM_NAME" --nvram 2>/dev/null || virsh undefine "$VM_NAME" 2>/dev/null || true
  pass "Domain '$VM_NAME' removed"
else
  info "No existing domain '$VM_NAME' — nothing to clean up"
fi

# ---- Reset libvirt default network ----
echo ""
echo "--- Resetting libvirt default network ---"
if virsh net-info default >/dev/null 2>&1; then
  virsh net-destroy default 2>/dev/null || true
  virsh net-undefine default 2>/dev/null || true
  info "Default network destroyed"
fi

virsh net-define /usr/share/libvirt/networks/default.xml 2>/dev/null || \
  fail "Could not define default network (is libvirt-daemon-system installed?)"
virsh net-autostart default
virsh net-start default
pass "Default network reset and started"

# ---- Download cloud image if missing ----
echo ""
echo "--- Base cloud image ---"
if [ -f "$CLOUD_IMAGE_PATH" ]; then
  info "Cloud image already exists at $CLOUD_IMAGE_PATH"
else
  info "Downloading Ubuntu 24.04 LTS cloud image..."
  wget -q --show-progress "$CLOUD_IMAGE_URL" -O "$CLOUD_IMAGE_PATH"
  pass "Downloaded $CLOUD_IMAGE_NAME"
fi

# ---- Create COW disk ----
echo ""
echo "--- VM disk ---"
qemu-img create -f qcow2 -F qcow2 -b "$CLOUD_IMAGE_PATH" "$VM_DISK_PATH" "${VM_DISK_GB}G"
pass "COW disk created: ${VM_DISK_PATH} (backed by ${CLOUD_IMAGE_NAME}, ${VM_DISK_GB}G)"

# ---- Create cloud-init seed ISO ----
echo ""
echo "--- Cloud-init seed ISO ---"
cloud-localds --network-config="$NETWORK_CONFIG" "$SEED_ISO_PATH" "$USER_DATA" "$META_DATA"
pass "Seed ISO created: ${SEED_ISO_PATH}"

# ---- Launch VM ----
echo ""
echo "--- Launching VM ---"
virt-install \
  --name "$VM_NAME" \
  --ram "$VM_RAM_MB" \
  --vcpus "$VM_VCPUS" \
  --disk path="$VM_DISK_PATH",format=qcow2 \
  --disk path="$SEED_ISO_PATH",device=cdrom \
  --os-variant ubuntu24.04 \
  --network "network=${VM_BRIDGE},model=virtio" \
  --graphics none \
  --console pty,target_type=virtio \
  --serial pty \
  --import \
  --noautoconsole

pass "VM '$VM_NAME' launched"

# ---- Wait for boot and print connection info ----
echo ""
echo "=============================================="
echo " VM '$VM_NAME' is booting (30-90s)."
echo ""
echo " To view the console:"
echo "   sudo virsh console $VM_NAME"
echo ""
echo " To find the IP (once booted):"
echo "   sudo virsh net-dhcp-leases default"
echo ""
echo " SSH in (after inserting your key in user-data.hardened.yaml):"
echo "   ssh ubuntu@<IP>"
echo ""
echo " Inside the VM, complete Phase 2:"
echo "   sudo tailscale up --ssh"
echo "   # then deploy VeloBid per docs/archive/phase1-finalization-runbook.md"
echo "=============================================="
