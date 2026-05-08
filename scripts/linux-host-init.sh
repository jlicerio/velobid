#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRV_ROOT="${VELOBID_SRV_ROOT:-/srv/velobid}"
ENV_FILE="${VELOBID_ENV_FILE:-$SRV_ROOT/secrets/velobid.env}"

require_root() {
  if [ "$(id -u)" -ne 0 ]; then
    echo "Run with sudo: sudo bash scripts/linux-host-init.sh" >&2
    exit 1
  fi
}

copy_seed_dir_once() {
  local source_dir="$1"
  local target_dir="$2"
  local marker="$target_dir/.seeded-from-repo"

  mkdir -p "$target_dir"
  if [ -f "$marker" ]; then
    echo "Already seeded: $target_dir"
    return
  fi

  if [ -d "$source_dir" ]; then
    cp -a "$source_dir/." "$target_dir/"
    touch "$marker"
    echo "Seeded $target_dir from $source_dir"
  else
    echo "Missing source directory: $source_dir" >&2
    exit 1
  fi
}

require_root

mkdir -p \
  "$SRV_ROOT/config" \
  "$SRV_ROOT/bid_projects" \
  "$SRV_ROOT/data/bids/api_generated" \
  "$SRV_ROOT/data/blueprints" \
  "$SRV_ROOT/data/files" \
  "$SRV_ROOT/data/configs" \
  "$SRV_ROOT/hermes" \
  "$SRV_ROOT/tailscale" \
  "$SRV_ROOT/backups" \
  "$SRV_ROOT/secrets"

copy_seed_dir_once "$ROOT_DIR/config" "$SRV_ROOT/config"
copy_seed_dir_once "$ROOT_DIR/bid_projects" "$SRV_ROOT/bid_projects"

if [ ! -f "$ENV_FILE" ]; then
  install -m 600 "$ROOT_DIR/env.production.example" "$ENV_FILE"
  echo "Created $ENV_FILE from env.production.example"
  echo "Edit $ENV_FILE and set HERMES_API_KEY plus HERMES_CREDENTIALS_JSON before deploying."
else
  chmod 600 "$ENV_FILE"
  echo "Existing env file kept: $ENV_FILE"
fi

chown -R root:root "$SRV_ROOT"
chmod 700 "$SRV_ROOT/secrets"
chmod 700 "$SRV_ROOT/backups"

echo "Linux host storage initialized at $SRV_ROOT"
