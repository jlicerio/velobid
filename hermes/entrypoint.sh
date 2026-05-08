#!/bin/bash
set -e

# Generate config.yaml from environment variables
cat > /root/.hermes/config.yaml << EOF
model:
  default: ${HERMES_MODEL:-deepseek-v4-flash}
  provider: ${HERMES_PROVIDER:-opencode-go}
  base_url: ${HERMES_BASE_URL:-https://opencode.ai/zen/go/v1}
EOF

echo "Generated config.yaml from environment variables"

# Generate auth.json from environment variable (JSON credential pool)
if [ -n "$HERMES_CREDENTIALS" ]; then
  echo "$HERMES_CREDENTIALS" > /root/.hermes/auth.json
  echo "Generated auth.json from HERMES_CREDENTIALS env var"
fi

# Copy auth.json to any existing profiles
if [ -d /root/.hermes/profiles ]; then
  for profile_dir in /root/.hermes/profiles/*/; do
    if [ -d "$profile_dir" ]; then
      cp /root/.hermes/auth.json "$profile_dir/auth.json" 2>/dev/null || true
    fi
  done
fi

# Copy admin server from image to runtime volume (image /root/.hermes is shadowed by volume)
cp /opt/admin_server.py /root/.hermes/admin_server.py 2>/dev/null || true

# Start admin server in background with nohup so it survives exec
nohup python3 /root/.hermes/admin_server.py > /tmp/admin-server.log 2>&1 &
echo "Admin server started on port ${ADMIN_PORT:-8640}"

# Give admin server a moment to start
sleep 1

# Execute the CMD (gateway run) — replaces this shell as PID 1
exec "$@"
