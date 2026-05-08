#!/bin/bash
set -e

# Ensure shared data directories exist (fresh docker volume)
mkdir -p /data/velobid/bids/api_generated
mkdir -p /data/velobid/blueprints
mkdir -p /data/velobid/files
mkdir -p /data/velobid/configs

echo "Ensured /data/velobid subdirectories exist"

# Execute the CMD (uvicorn)
exec "$@"
