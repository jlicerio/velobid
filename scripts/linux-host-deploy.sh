#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRV_ROOT="${VELOBID_SRV_ROOT:-/srv/velobid}"
ENV_FILE="${VELOBID_ENV_FILE:-$SRV_ROOT/secrets/velobid.env}"
COMPOSE_FILE="$ROOT_DIR/docker-compose.host.yml"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

wait_for_http() {
  local name="$1"
  local url="$2"
  local header="${3:-}"

  for _ in $(seq 1 40); do
    if [ -n "$header" ]; then
      if curl -fsS -H "$header" "$url" >/dev/null; then
        echo "PASS: $name"
        return 0
      fi
    else
      if curl -fsS "$url" >/dev/null; then
        echo "PASS: $name"
        return 0
      fi
    fi
    sleep 3
  done

  echo "FAIL: $name did not become healthy at $url" >&2
  return 1
}

require_command docker
require_command curl

if [ ! -f "$ENV_FILE" ]; then
  echo "Missing $ENV_FILE. Run: sudo bash scripts/linux-host-init.sh" >&2
  exit 1
fi

if [ ! -r "$ENV_FILE" ]; then
  echo "Cannot read $ENV_FILE. Run deploy with sudo or adjust VELOBID_ENV_FILE permissions." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
. "$ENV_FILE"
set +a

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" build
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps

API_BIND="${VELOBID_BIND_ADDR:-0.0.0.0}"
API_HOST="$API_BIND"
if [ "$API_HOST" = "0.0.0.0" ]; then
  API_HOST="127.0.0.1"
fi

HERMES_BIND="${HERMES_BIND_ADDR:-127.0.0.1}"
HERMES_HOST="$HERMES_BIND"
if [ "$HERMES_HOST" = "0.0.0.0" ]; then
  HERMES_HOST="127.0.0.1"
fi

wait_for_http "VeloBid API" "http://$API_HOST:${VELOBID_PORT:-8000}/api/v1/meta"
wait_for_http "VeloBid health" "http://$API_HOST:${VELOBID_PORT:-8000}/api/v1/health"
wait_for_http "Hermes gateway" "http://$HERMES_HOST:${HERMES_PORT:-8644}/v1/models" "Authorization: Bearer ${HERMES_API_KEY:-velobid-internal}"

echo "Deployment complete."
