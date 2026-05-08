#!/usr/bin/env bash
# =============================================================================
# VeloBid — Phase 1 VM Bootstrap: verify-phase1.sh
# Purpose:  Run INSIDE the Phase 1 VM (or via SSH) to verify all bootstrap
#           services are installed and running correctly.
# Usage:    bash verify-phase1.sh
#
# Gates:    Every check prints PASS or FAIL.  If ANY check fails the script
#           exits with code 1.  Expected state after Phase 1:
#             - SSH is running and hardened (PasswordAuthentication no)
#             - qemu-guest-agent is active
#             - Docker CE is installed and the daemon is running
#             - Tailscale CLI is installed but NOT yet authenticated
#             - UFW is active and allows SSH
#             - fail2ban is running
# =============================================================================

set -u   # no -e: we want to count failures, not abort on first error

FAILED=0

red='\033[0;31m'
green='\033[0;32m'
nc='\033[0m'

pass() { echo -e "  ${green}[PASS]${nc} $1"; }
fail() { echo -e "  ${red}[FAIL]${nc} $1"; FAILED=$((FAILED + 1)); }

# =============================================================================
echo "=============================================="
echo " VeloBid Phase 1 — Bootstrap Verification"
echo "=============================================="
echo ""

# ---- SSH ----
echo "--- SSH ---"

if systemctl is-active --quiet ssh; then
  pass "ssh service is running"
else
  fail "ssh service is NOT running"
fi

if grep -qs '^PasswordAuthentication no' /etc/ssh/sshd_config; then
  pass "PasswordAuthentication is set to no"
else
  fail "PasswordAuthentication is NOT disabled in /etc/ssh/sshd_config"
fi

if grep -qs '^PermitRootLogin prohibit-password' /etc/ssh/sshd_config; then
  pass "PermitRootLogin is set to prohibit-password"
else
  fail "PermitRootLogin is NOT set to prohibit-password"
fi

echo ""
# ---- qemu-guest-agent ----
echo "--- qemu-guest-agent ---"

if systemctl is-active --quiet qemu-guest-agent; then
  pass "qemu-guest-agent is running"
else
  fail "qemu-guest-agent is NOT running"
fi

if systemctl is-enabled --quiet qemu-guest-agent 2>/dev/null; then
  pass "qemu-guest-agent is enabled"
else
  fail "qemu-guest-agent is NOT enabled"
fi

echo ""
# ---- Docker ----
echo "--- Docker ---"

if command -v docker &>/dev/null; then
  pass "docker CLI is installed ($(docker --version))"
else
  fail "docker CLI is NOT installed"
fi

if systemctl is-active --quiet docker; then
  pass "docker daemon is running"
else
  fail "docker daemon is NOT running"
fi

if docker compose version &>/dev/null; then
  pass "docker compose plugin is installed ($(docker compose version --short 2>/dev/null || echo 'ok'))"
else
  fail "docker compose plugin is NOT installed"
fi

echo ""
# ---- Tailscale ----
echo "--- Tailscale ---"

if command -v tailscale &>/dev/null; then
  pass "tailscale CLI is installed ($(tailscale version 2>/dev/null | head -1))"
else
  fail "tailscale CLI is NOT installed"
fi

# Expected state after Phase 1: NOT authenticated (manual step still required)
if tailscale status >/dev/null 2>&1; then
  fail "tailscale IS authenticated already — this should be a manual Phase 2 step"
else
  pass "tailscale is NOT yet authenticated (expected — run 'sudo tailscale up --ssh' manually)"
fi

echo ""
# ---- UFW ----
echo "--- UFW ---"

if command -v ufw &>/dev/null; then
  pass "ufw is installed"
else
  fail "ufw is NOT installed"
fi

if ufw status | grep -qi 'active'; then
  pass "ufw is active"
else
  fail "ufw is NOT active"
fi

if ufw status | grep -qE '22/tcp.*ALLOW'; then
  pass "ufw allows SSH (port 22/tcp)"
else
  fail "ufw does NOT allow SSH (port 22/tcp)"
fi

echo ""
# ---- fail2ban ----
echo "--- fail2ban ---"

if systemctl is-active --quiet fail2ban; then
  pass "fail2ban is running"
else
  fail "fail2ban is NOT running"
fi

if systemctl is-enabled --quiet fail2ban 2>/dev/null; then
  pass "fail2ban is enabled"
else
  fail "fail2ban is NOT enabled"
fi

echo ""
# ---- Tools & connectivity ----
echo "--- General tools ---"

for tool in curl git jq htop; do
  if command -v "$tool" &>/dev/null; then
    pass "$tool is installed"
  else
    fail "$tool is NOT installed"
  fi
done

echo ""
# ---- /etc/hostname ----
echo "--- Host identity ---"

EXPECTED_HOSTNAME="velobid"
CURRENT_HOSTNAME="$(hostname)"
if [ "$CURRENT_HOSTNAME" = "$EXPECTED_HOSTNAME" ]; then
  pass "hostname is '$EXPECTED_HOSTNAME'"
else
  fail "hostname is '$CURRENT_HOSTNAME' (expected '$EXPECTED_HOSTNAME')"
fi

# =============================================================================
echo ""
echo "=============================================="
if [ "$FAILED" -eq 0 ]; then
  echo "  ${green}ALL CHECKS PASSED.  Phase 1 bootstrap is complete.${nc}"
  echo "  Proceed to Phase 2: sudo tailscale up --ssh"
  echo "=============================================="
  exit 0
else
  echo "  ${red}${FAILED} CHECK(S) FAILED.  Review output above.${nc}"
  echo "=============================================="
  exit 1
fi
