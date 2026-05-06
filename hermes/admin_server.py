#!/usr/bin/env python3
"""
Lightweight admin server for bidder profile management inside the Hermes container.
Runs alongside the Hermes gateway to handle profile CRUD via HTTP,
eliminating the need for Docker exec from VeloBid.

Endpoints:
  POST /admin/profiles  — Create a bidder profile
  GET  /admin/health    — Health check
"""
import json
import logging
import os
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

logging.basicConfig(level=logging.INFO, format="%(asctime)s admin %(message)s")
logger = logging.getLogger("admin")

HERMES_HOME = os.environ.get("HERMES_HOME", "/root/.hermes")
ADMIN_PORT = int(os.environ.get("ADMIN_PORT", "8640"))


def _run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def create_profile(body: dict) -> dict:
    bidder_id = body.get("bidder_id")
    company_name = body.get("company_name", "Unknown")
    trades = body.get("trades", [])
    company_context = body.get("company_context", "")
    pricing = body.get("pricing", {})

    if not bidder_id:
        return {"error": "bidder_id is required"}

    profile_name = f"bidder-{bidder_id}"

    # 1. Create Hermes profile
    _run(["hermes", "profile", "create", profile_name])

    # 2. Write SOUL.md
    soul = f"""# {company_name}

You are the AI estimating assistant for {company_name}.
Specialties: {', '.join(trades)}
Service area: {body.get('service_area', 'Nationwide')}

## Company Context
{company_context}

## Communication Style
- Professional, precise construction estimating language
- Always cite specific line items and costs
- Flag exclusions and assumptions clearly
- Respond in the same language the user writes in
"""
    with open(f"{HERMES_HOME}/profiles/{profile_name}/SOUL.md", "w") as f:
        f.write(soul)

    # 3. Write pricing skill
    skill_dir = f"{HERMES_HOME}/profiles/{profile_name}/skills/bidder-pricing"
    os.makedirs(skill_dir, exist_ok=True)
    pricing_skill = f"""---
name: {profile_name}-pricing
description: Pricing defaults for {company_name}
---

## Pricing Defaults
- Labor rate: ${pricing.get('labor_rate', 65.0)}/hr
- Equipment markup: {pricing.get('equipment_markup_pct', 10.0)}%
- Overhead & profit: {pricing.get('overhead_profit_pct', 15.0)}%
- Contingency: {pricing.get('contingency_pct', 5.0)}%
- Tax rate: {pricing.get('tax_rate', 0.0825)}
"""
    with open(f"{skill_dir}/SKILL.md", "w") as f:
        f.write(pricing_skill)

    # 4. Write file management skill
    fm_dir = f"{HERMES_HOME}/profiles/{profile_name}/skills/file-mgmt"
    os.makedirs(fm_dir, exist_ok=True)
    fm_skill = f"""---
name: {profile_name}-file-mgmt
description: File locations for {company_name}
---

## File Locations
- Blueprints: /data/velobid/blueprints/{profile_name}/{{project_id}}/
- Generated bids: /data/velobid/bids/{profile_name}/{{project_id}}/
- Company config: /data/velobid/configs/{profile_name}.json
"""
    with open(f"{fm_dir}/SKILL.md", "w") as f:
        f.write(fm_skill)

    # 5. Copy auth.json
    auth_src = f"{HERMES_HOME}/auth.json"
    auth_dst = f"{HERMES_HOME}/profiles/{profile_name}/auth.json"
    if os.path.exists(auth_src):
        _run(["cp", auth_src, auth_dst])

    logger.info("Created profile %s for %s", profile_name, company_name)
    return {"profile_name": profile_name, "status": "created"}


class AdminHandler(BaseHTTPRequestHandler):
    def _json(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        if self.path == "/admin/health":
            self._json({"status": "ok"})
        elif self.path.startswith("/admin/profiles/") and self.path.endswith("/soul"):
            profile_name = self.path.split("/")[3]
            soul_path = f"{HERMES_HOME}/profiles/{profile_name}/SOUL.md"
            if os.path.exists(soul_path):
                with open(soul_path) as f:
                    self._json({"content": f.read()})
            else:
                self._json({"error": "not found"}, 404)
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        if self.path == "/admin/profiles":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            try:
                result = create_profile(body)
                self._json(result, 201 if result.get("status") == "created" else 400)
            except Exception as e:
                logger.error("Profile creation failed: %s", e)
                self._json({"error": str(e)}, 500)
        else:
            self._json({"error": "not found"}, 404)

    def log_message(self, fmt, *args):
        logger.info(fmt, *args)


def main():
    server = HTTPServer(("0.0.0.0", ADMIN_PORT), AdminHandler)
    logger.info("Admin server listening on port %d", ADMIN_PORT)
    server.serve_forever()


if __name__ == "__main__":
    main()
