#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRV_ROOT="${VELOBID_SRV_ROOT:-/srv/velobid}"
ENV_FILE="${VELOBID_ENV_FILE:-$SRV_ROOT/secrets/velobid.env}"
HOST_COMPOSE="$ROOT_DIR/docker-compose.host.yml"
TAILSCALE_COMPOSE="$ROOT_DIR/docker-compose.tailscale.yml"
TAILSCALE_STATE_DIR="${TAILSCALE_STATE_DIR:-$SRV_ROOT/tailscale}"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

require_command docker
require_command curl

if [ ! -r "$ENV_FILE" ]; then
  echo "Cannot read $ENV_FILE. Run with sudo or initialize host storage first." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
. "$ENV_FILE"
set +a

mkdir -p "$TAILSCALE_STATE_DIR"

if [ -z "${TAILSCALE_AUTHKEY:-}" ] && [ ! -f "$TAILSCALE_STATE_DIR/tailscaled.state" ]; then
  echo "TAILSCALE_AUTHKEY is required for first container login." >&2
  echo "Create a reusable or ephemeral auth key in Tailscale, then set it in $ENV_FILE." >&2
  exit 1
fi

docker compose \
  --env-file "$ENV_FILE" \
  -f "$HOST_COMPOSE" \
  -f "$TAILSCALE_COMPOSE" \
  up -d velobid velobid-tailscale velobid-tailnet-proxy

for _ in $(seq 1 40); do
  if docker exec velobid-tailscale tailscale status >/dev/null 2>&1; then
    break
  fi
  sleep 3
done

docker exec velobid-tailscale tailscale serve --bg http://127.0.0.1:8080
docker exec velobid-tailscale tailscale serve status

TAILSCALE_HOST="${TAILSCALE_HOSTNAME:-velobid}"
TAILNET="${TAILSCALE_TAILNET:-tailfceaca.ts.net}"
URL="https://$TAILSCALE_HOST.$TAILNET"

echo "Container Tailscale Serve configured."
echo "Expected tailnet URL: $URL/projects"
echo "Verify from a tailnet client:"
echo "  curl -fsS $URL/api/v1/health"
