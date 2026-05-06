# VeloBid Multi-Tenant Hermes Architecture

## Current State (native Hermes, single tenant)

```
Browser ── HTTPS ──> VeloBid (Docker :8000)
                        │
                   POST /api/v1/agent/chat
                        │ proxy via httpx
                        ▼
               Hermes API Server (systemd :8643)
                  └── air-hero profile (single tenant)
```

Hermes runs natively on the Linux host as a systemd service. The `air-hero` profile serves all bidder groups through one set of skills/memory. Files (blueprints, generated PDFs) are on the host filesystem.

## Target Architecture: Multi-Tenant with Docker

```
Browser ── HTTPS ──> VeloBid (Docker :8000)
                        │
                   POST /api/v1/agent/chat
                   (forwarded with bidder_id)
                        │
                        ▼
               VeloBid Router (/api/v1/agent/chat)
                  │                              │
                  │  bidder="acme_hvac"           │  bidder="prestige_elec"
                  ▼                              ▼
     Hermes API (container)           Hermes API (container)
     :8643 / acme profile             :8644 / prestige profile
        ├── acme SOUL.md                 ├── prestige SOUL.md
        ├── Skills: hvac-pricing         ├── Skills: electrical-pricing
        ├── Memory: acme context         ├── Memory: prestige context
        └── Sessions: acme/              └── Sessions: prestige/
```

**Two possible approaches for multi-tenant Hermes:**

| Approach | Pros | Cons |
|----------|------|------|
| **A: One Hermes container, multiple profiles** | Single container to manage, lighter | Profiles share container resources, need inter-profile isolation |
| **B: One Hermes container per bidder** | Full isolation, scales independently | More containers, heavier orchestration |

**Recommendation: Start with A** (single container, multiple profiles). It's simpler, matches how Hermes profiles were designed to work, and scales fine for dozens of bidders. Move to B only if you need resource isolation between tenants.

---

## I. Hermes Container

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Install Hermes Agent
RUN curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

# Copy config (auth.json, config.yaml, .env)
COPY config/ /root/.hermes/

# Expose API server (start at 8642, one per profile)
EXPOSE 8642-8700

# Entry: start gateway with API server
CMD ["hermes", "gateway", "run"]
```

### docker-compose.yml (Phase 1 — single Hermes, multi-profile)

```yaml
services:
  velobid:
    build: .
    container_name: velobid
    restart: unless-stopped
    ports:
      - "0.0.0.0:8000:8000"
    volumes:
      - ./api/static:/app/api/static
      - ./config:/app/config
      - ./bid_projects:/app/bid_projects
      - ./.env:/app/.env:ro
      - shared_data:/data/velobid
    depends_on:
      - hermes

  hermes:
    build: ./hermes
    container_name: hermes
    restart: unless-stopped
    ports:
      - "127.0.0.1:8642:8642"
    volumes:
      - hermes_data:/root/.hermes       # Persistent profiles, sessions, memory
      - shared_data:/data/velobid       # Shared file storage
      - ./hermes/config:/root/.hermes/config:ro
      - ./hermes/auth.json:/root/.hermes/auth.json:ro
      - ./hermes/.env:/root/.hermes/.env:ro
    environment:
      - API_SERVER_ENABLED=true
      - API_SERVER_HOST=0.0.0.0
      - API_SERVER_PORT=8642
      - API_SERVER_KEY=${HERMES_API_KEY}
      - HERMES_HOME=/root/.hermes

volumes:
  shared_data:
  hermes_data:
```

### Startup script (entrypoint.sh)

The container needs to:
1. Copy auth.json to each profile that exists
2. Start the gateway

```bash
#!/bin/bash
# Copy credential pool to all profiles
for profile_dir in /root/.hermes/profiles/*/; do
  if [ -d "$profile_dir" ] && [ ! -f "${profile_dir}auth.json" ]; then
    cp /root/.hermes/auth.json "${profile_dir}auth.json"
  fi
done

# Start gateway
exec hermes gateway run
```

---

## II. VeloBid → Hermes Routing

### Current proxy (single tenant)

Currently VeloBid proxies all chat to one Hermes profile:

```python
HERMES_URL = "http://host.docker.internal:8643/v1/chat/completions"
```

### Target (multi-tenant)

VeloBid routes to the correct Hermes profile based on `bidder_id`:

```python
# In VeloBid's chat endpoint
@app.post("/api/v1/agent/chat")
async def agent_chat(request: ChatRequest):
    bidder_id = request.bidder_id or get_bidder_from_session()
    profile_name = f"bidder-{bidder_id}"

    hermes_url = f"http://hermes:8642/v1/chat/completions"
    model_name = profile_name  # API server routes by model name → profile

    payload = {
        "model": model_name,
        "messages": request.messages,
        "stream": True,
    }

    # Proxy SSE stream
    return await proxy_to_hermes(hermes_url, payload)
```

The Hermes API server uses the `model` field to select which profile handles the request. So VeloBid passes `"model": "bidder-acme_hvac"` and Hermes routes to that profile's agent.

---

## III. Profile Auto-Creation

When a new bidder registers in VeloBid:

### Flow

```
1. Bidder signs up in VeloBid
2. VeloBid creates bidder config (company info, trades, pricing)
3. VeloBid calls Hermes admin API to create profile
4. Hermes creates profile + writes SOUL.md + skills
5. VeloBid gets profile name back, stores it with bidder record
```

### Hermes Admin Endpoint

Hermes doesn't have a built-in profile-creation API, so we add one via a lightweight admin service (or call the CLI from within the container):

```python
# Admin service running alongside Hermes (or as a FastAPI route in VeloBid)
import subprocess, json, os

HERMES_HOME = "/root/.hermes"

async def create_bidder_profile(bidder_id: str, config: dict):
    """
    Create a Hermes profile for a new bidder.
    """
    profile_name = f"bidder-{bidder_id}"

    # 1. Create the Hermes profile
    subprocess.run(["hermes", "profile", "create", profile_name], check=True)

    # 2. Write SOUL.md — bidder identity
    soul = f"""# {config['company_name']}

You are the AI estimating assistant for {config['company_name']}.
Specialties: {', '.join(config['trades'])}
Service area: {config.get('service_area', 'Nationwide')}

## Company Context
{config.get('company_context', '')}

## Communication Style
- Professional, precise construction estimating language
- Always cite specific line items and costs
- Flag exclusions and assumptions clearly
"""
    write_file(f"{HERMES_HOME}/profiles/{profile_name}/SOUL.md", soul)

    # 3. Write pricing skill — bidder's pricing defaults
    pricing_skill = f"""---
name: {profile_name}-pricing
description: Pricing defaults for {config['company_name']}
---

## Pricing Defaults
- Labor rate: ${config['default_labor_rate']}/hr
- Equipment markup: {config['default_equipment_markup_pct']}%
- Overhead & profit: {config['default_overhead_profit_pct']}%
- Contingency: {config['default_contingency_pct']}%
- Tax rate: {config['default_tax_rate']}
"""
    skill_dir = f"{HERMES_HOME}/profiles/{profile_name}/skills/"
    os.makedirs(skill_dir, exist_ok=True)
    write_file(f"{skill_dir}/bidder-pricing/SKILL.md", pricing_skill)

    # 4. Copy auth.json (critical — profiles don't inherit credentials)
    subprocess.run([
        "cp", f"{HERMES_HOME}/auth.json",
        f"{HERMES_HOME}/profiles/{profile_name}/auth.json"
    ], check=True)

    # 5. Set profile's model config to the default
    subprocess.run([
        "hermes", "-p", profile_name, "config", "set",
        "model.default", "deepseek-v4-flash"
    ])
    subprocess.run([
        "hermes", "-p", profile_name, "config", "set",
        "model.provider", "opencode-go"
    ])

    return profile_name
```

### Triggers

The auto-creation can be triggered by:

1. **VeloBid API webhook** — when a bidder record is created, VeloBid POSTs to Hermes admin endpoint
2. **VeloBid callback** — VeloBid calls the profile creation directly during signup flow
3. **CLI script** — `./scripts/create-bidder-profile.sh <bidder_id> <config.json>`

---

## IV. File Management

### Shared Volume Structure

```
/data/velobid/
  ├── blueprints/
  │   ├── acme_hvac/
  │   │   ├── project-123/
  │   │   │   ├── hvac-plans.pdf
  │   │   │   └── scope-of-work.pdf
  │   │   └── project-456/
  │   └── prestige_elec/
  ├── bids/
  │   ├── acme_hvac/
  │   │   └── project-123/
  │   │       ├── client-bid-v1.pdf
  │   │       └── internal-bid-v1.pdf
  │   └── prestige_elec/
  └── configs/
      ├── acme_hvac.json
      └── prestige_elec.json
```

### Access Patterns

| Operation | Owner | Path |
|-----------|-------|------|
| Upload blueprint | VeloBid API → writes | `/data/velobid/blueprints/{bidder}/{project}/` |
| Read blueprint for vision | Hermes reads | `/data/velobid/blueprints/{bidder}/{project}/` |
| Generate bid PDF | Hermes writes | `/data/velobid/bids/{bidder}/{project}/` |
| Serve bid PDF to user | VeloBid reads | `/data/velobid/bids/{bidder}/{project}/` |
| Read bidder config | Both | `/data/velobid/configs/{bidder}.json` |

### File Management Hermes Skill

A skill for each profile tells Hermes where to read/write files:

```markdown
## File Locations
- Blueprints: /data/velobid/blueprints/{bidder_id}/
- Generated bids: /data/velobid/bids/{bidder_id}/
- Company configs: /data/velobid/configs/{bidder_id}.json
```

---

## V. VeloBid Proxy Implementation

The existing chat proxy in VeloBid gets upgraded from single-tenant to multi-tenant:

```python
# api/services/hermes.py (new service module)
import httpx, os

HERMES_INTERNAL_URL = os.getenv("HERMES_URL", "http://hermes:8642")
HERMES_API_KEY = os.getenv("HERMES_API_KEY")

async def proxy_chat_to_hermes(
    messages: list,
    bidder_id: str,
    stream: bool = True,
):
    profile_name = f"bidder-{bidder_id}"

    payload = {
        "model": profile_name,
        "messages": messages,
        "stream": stream,
    }

    headers = {"Authorization": f"Bearer {HERMES_API_KEY}"}

    async with httpx.AsyncClient(timeout=300) as client:
        async with client.stream(
            "POST",
            f"{HERMES_INTERNAL_URL}/v1/chat/completions",
            json=payload,
            headers=headers,
        ) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    yield line
```

---

## VI. Kubernetes Migration Path

### Phase 1: Docker Compose (Now)

```yaml
services:
  velobid:    # Single replica
  hermes:     # Single replica, all profiles
  volumes:
    shared_data    # NFS or local volume
    hermes_data    # Profile data, sessions, memory
```

### Phase 2: Docker Compose, multiple Hermes (Next step)

For heavy bidders that need dedicated resources:

```yaml
services:
  velobid:
  hermes:           # Default profiles
  hermes-acme:      # Dedicated for high-volume bidder
  hermes-prestige:  # Dedicated for high-volume bidder
```

### Phase 3: Kubernetes

```
┌──────────────────────────────────────────────┐
│  K8s Cluster                                 │
│                                               │
│  ┌──────────────┐  ┌──────────────────────┐  │
│  │ VeloBid       │  │ Hermes (StatefulSet) │  │
│  │ Deployment    │  │ Replicas: 1-3       │  │
│  │ HPA: CPU>70% │  │ Profiles on PVC     │  │
│  │ No local FS  │  │                      │  │
│  └──────┬───────┘  └──────────┬───────────┘  │
│         │                     │              │
│         └─────────┬───────────┘              │
│                   ▼                          │
│         ┌──────────────────┐                 │
│         │  Shared PVC      │                 │
│         │  (ReadWriteMany) │                 │
│         │  blueprints/     │                 │
│         │  bids/           │                 │
│         │  configs/        │                 │
│         └──────────────────┘                 │
│                                               │
│  ┌──────────────────────┐                    │
│  │ Ingress (Tailscale)  │                    │
│  │ velobid.example.com  │                    │
│  └──────────────────────┘                    │
└──────────────────────────────────────────────┘
```

**Key K8s changes from Docker:**
- **VeloBid** → Deployment + HPA (stateless, scales horizontally)
- **Hermes** → StatefulSet (needs stable identity for profile sessions)
- **Shared storage** → ReadWriteMany PVC (NFS, Longhorn, or EFS)
- **Profile auto-creation** → Init container or operator that watches a ConfigMap for new bidder configs and runs `hermes profile create`

---

## VII. Implementation Phases

### Phase 1: Hermes Container + API Routing (1-2 days)

| Task | Details |
|------|---------|
| Write Hermes Dockerfile | Python 3.11-slim + Hermes install |
| Create docker-compose with both services | Hermes + VeloBid in one compose file |
| Wire up VeloBid → Hermes proxy | Update `/api/v1/agent/chat` to call `http://hermes:8642` |
| Set up shared volume | Mount `/data/velobid` in both containers |
| Migrate existing profile | Convert `air-hero` to `bidder-air_hero` in containerized Hermes |
| Smoke test | Chat, blueprint upload, bid generation end-to-end |

### Phase 2: Profile Auto-Creation (1-2 days)

| Task | Details |
|------|---------|
| Build profile creation script | `create-bidder-profile.sh` template |
| Wire into VeloBid signup | API endpoint triggers profile creation |
| Create SOUL.md + skill template | Per-bidder pricing context, trade specializations |
| Write admin endpoint | Lightweight FastAPI or CLI wrapper for profile CRUD |

### Phase 3: File Management (1 day)

| Task | Details |
|------|---------|
| Define shared volume structure | `/{blueprints,bids,configs}/{bidder}/{project}/` |
| Update Hermes skills | Each bidder profile knows its file paths |
| Update VeloBid file handlers | Upload/read from shared volume |
| Clean up old host-only paths | Remove stale native-file references |

### Phase 4: K8s Prep (2-3 days)

| Task | Details |
|------|---------|
| Containerize VeloBid for K8s | Health checks, env config, no host dependencies |
| Hermes StatefulSet manifests | PVC for profiles, readiness probe |
| Shared PVC setup | NFS server or cloud-native storage |
| Ingress + TLS | Tailscale or standard ingress |
| Profile auto-creation via operator | Watch ConfigMap, create profiles |


## VIII. Open Questions

| Question | Options | Decision |
|----------|---------|----------|
| Profile per bidder or per trade? | Per-bidder (group of users) vs per-trade (hvac, elec) | **Per-bidder** — one profile per company |
| Shared Hermes or per-bidder containers? | Single container multi-profile vs per-bidder container | **Start with single** — simpler, profiles handle isolation |
| How does Hermes API route to profiles? | `model` field in chat completions maps to profile name | Use `"model": "bidder-{id}"` convention |
| Who manages the profile creation? | VeloBid admin UI vs CLI script vs Hermes admin endpoint | **Start with CLI**, then add API |
| Shared storage backend? | Docker volume vs NFS vs S3 | **Docker volume** for Phase 1, NFS for Phase 3 |
| How to handle Hermes API key rotation? | Key per profile vs one global key | **One global key** for Phase 1, rotate via .env |
