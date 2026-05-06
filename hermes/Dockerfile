FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl git xz-utils && rm -rf /var/lib/apt/lists/*

# Install uv (fast Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    . $HOME/.local/bin/env

# Clone Hermes repo and install Python deps (skip Node.js/browser tools — API server only)
RUN . $HOME/.local/bin/env && \
    git clone --depth 1 https://github.com/NousResearch/hermes-agent.git /opt/hermes-agent && \
    cd /opt/hermes-agent && \
    uv venv && \
    uv sync --frozen --no-dev

# Symlink hermes binary
RUN ln -sf /opt/hermes-agent/.venv/bin/hermes /usr/local/bin/hermes

# Copy entrypoint and config
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY admin_server.py /opt/admin_server.py

RUN mkdir -p /root/.hermes/profiles
COPY config/config.yaml /root/.hermes/config.yaml
COPY config/.env /root/.hermes/.env
COPY auth.json /root/.hermes/auth.json

EXPOSE 8642

ENTRYPOINT ["/entrypoint.sh"]
CMD ["hermes", "gateway", "run"]
