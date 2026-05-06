#!/bin/bash
set -e

# Start Tailscale if TS_AUTH_KEY is provided
if [ -n "$TS_AUTH_KEY" ]; then
    echo "Starting Tailscale..."
    tailscaled --state=/var/lib/tailscale/tailscaled.state --socket=/var/run/tailscale/tailscaled.sock &
    sleep 2
    tailscale up --authkey="$TS_AUTH_KEY" --hostname="${TS_HOSTNAME:-velobid}" --accept-routes=false
    echo "Tailscale connected: $(tailscale ip -4)"
else
    echo "No TS_AUTH_KEY set, running without Tailscale"
fi

# Start VeloBid
echo "Starting VeloBid..."
exec uvicorn api.main:app --host 0.0.0.0 --port 8000
