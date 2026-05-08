#!/usr/bin/env bash
set -euo pipefail

SRV_ROOT="${VELOBID_SRV_ROOT:-/srv/velobid}"
ENV_FILE="${VELOBID_ENV_FILE:-$SRV_ROOT/secrets/velobid.env}"
BACKUP_DIR="${VELOBID_BACKUP_DIR:-$SRV_ROOT/backups}"
RETAIN_LOCAL_BACKUPS="${VELOBID_RETAIN_LOCAL_BACKUPS:-14}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
ARCHIVE="$BACKUP_DIR/velobid-$STAMP.tar.gz"

if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
fi

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

tar \
  --create \
  --gzip \
  --file "$ARCHIVE" \
  --directory "$SRV_ROOT" \
  config \
  bid_projects \
  data \
  hermes \
  tailscale

sha256sum "$ARCHIVE" > "$ARCHIVE.sha256"
echo "Created local backup: $ARCHIVE"

find "$BACKUP_DIR" -maxdepth 1 -name 'velobid-*.tar.gz' -type f \
  | sort -r \
  | tail -n +"$((RETAIN_LOCAL_BACKUPS + 1))" \
  | xargs -r rm -f
find "$BACKUP_DIR" -maxdepth 1 -name 'velobid-*.tar.gz.sha256' -type f \
  | sort -r \
  | tail -n +"$((RETAIN_LOCAL_BACKUPS + 1))" \
  | xargs -r rm -f

if [ -n "${RESTIC_REPOSITORY:-}" ] && [ -n "${RESTIC_PASSWORD:-}" ]; then
  if ! command -v restic >/dev/null 2>&1; then
    echo "RESTIC_REPOSITORY is set, but restic is not installed. Local backup still succeeded." >&2
    exit 0
  fi

  restic snapshots >/dev/null 2>&1 || restic init
  restic backup "$SRV_ROOT/config" "$SRV_ROOT/bid_projects" "$SRV_ROOT/data" "$SRV_ROOT/hermes" "$SRV_ROOT/tailscale"
  restic forget --keep-daily "$RETAIN_LOCAL_BACKUPS" --prune
  echo "Restic offsite backup complete."
fi
