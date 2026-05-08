#!/usr/bin/env bash
set -euo pipefail

SRV_ROOT="${VELOBID_SRV_ROOT:-/srv/velobid}"
BACKUP_PATH="${1:-}"
MODE="${2:-preview}"
RESTORE_ROOT="$SRV_ROOT/restore-preview/$(date -u +%Y%m%dT%H%M%SZ)"

usage() {
  echo "Usage:"
  echo "  sudo bash scripts/linux-host-restore.sh /srv/velobid/backups/velobid-YYYYmmddTHHMMSSZ.tar.gz"
  echo "  sudo bash scripts/linux-host-restore.sh /srv/velobid/backups/velobid-YYYYmmddTHHMMSSZ.tar.gz --apply"
}

if [ -z "$BACKUP_PATH" ]; then
  usage >&2
  exit 1
fi

if [ ! -f "$BACKUP_PATH" ]; then
  echo "Backup archive not found: $BACKUP_PATH" >&2
  exit 1
fi

if [ -f "$BACKUP_PATH.sha256" ]; then
  sha256sum -c "$BACKUP_PATH.sha256"
fi

if [ "$MODE" = "--apply" ]; then
  echo "Applying restore to $SRV_ROOT"
  echo "This overwrites config, bid_projects, data, hermes, and tailscale from the backup."
  read -r -p "Type RESTORE to continue: " CONFIRM
  if [ "$CONFIRM" != "RESTORE" ]; then
    echo "Restore cancelled."
    exit 1
  fi

  tar --extract --gzip --file "$BACKUP_PATH" --directory "$SRV_ROOT"
  echo "Restore applied. Restart containers with scripts/linux-host-deploy.sh."
else
  mkdir -p "$RESTORE_ROOT"
  tar --extract --gzip --file "$BACKUP_PATH" --directory "$RESTORE_ROOT"
  echo "Restore preview extracted to: $RESTORE_ROOT"
  echo "Inspect this directory before using --apply."
fi
