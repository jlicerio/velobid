# VeloBid Development Workflow

This guide covers the containerized development path for VeloBid.

## Recommended local setup

Use the dev compose file when you want live source sync and browser refreshes:

```bash
docker compose -f docker-compose.dev.yml up --build
```

If you prefer `make`, use:

```bash
make dev-up
```

Services:

- `velobid`: FastAPI backend with `uvicorn --reload` on port `8000`
- `frontend`: Vite dev server on port `5173`
- `hermes` (optional): start with `--profile hermes` when you need the chat/AI path

Open the UI at `http://127.0.0.1:5173` and the API at `http://127.0.0.1:8000`.

Example:

```bash
docker compose -f docker-compose.dev.yml --profile hermes up --build
```

The frontend proxy target is controlled by `VITE_API_PROXY_TARGET` and defaults to the backend container name in dev mode.

## Production path

Use the Linux host deploy path for the real containerized stack:

```bash
sudo bash scripts/linux-host-deploy.sh
```

Do not rely on the dev compose file for production deploys.

## Fast iteration loop

1. Edit frontend or backend source.
2. Let the dev containers hot-reload.
3. Run `python scripts/verify.py --live --frontend-url http://127.0.0.1:5173` when you want a quick smoke check.
