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
    service_area = body.get("service_area", "Nationwide")
    pricing = body.get("pricing", {})

    if not bidder_id:
        return {"error": "bidder_id is required"}

    profile_name = f"bidder-{bidder_id}"
    profile_dir = f"{HERMES_HOME}/profiles/{profile_name}"
    template_dir = f"{HERMES_HOME}/profiles/bidder-velobid"

    # Clone from template if available, otherwise create fresh
    if os.path.isdir(template_dir) and bidder_id != "velobid":
        _run(["cp", "-r", template_dir, profile_dir])
        logger.info("Cloned profile %s from template", profile_name)
    else:
        _run(["hermes", "profile", "create", profile_name])
        logger.info("Created fresh profile %s", profile_name)

    # Customize SOUL.md — prepend bidder info to template
    soul_header = f"""# {company_name}

You are the AI estimating assistant for {company_name}.
Specialties: {', '.join(trades) if trades else 'General Contracting'}
Service area: {service_area}

## Company Context
{company_context}

"""
    soul_path = f"{profile_dir}/SOUL.md"
    existing = ""
    if os.path.exists(soul_path):
        with open(soul_path) as f:
            existing = f.read()
        # Skip header if already has a # heading
        if existing.startswith("# "):
            # Replace first heading with bidder-specific header
            parts = existing.split("\n", 1)
            existing = parts[1] if len(parts) > 1 else ""

    with open(soul_path, "w") as f:
        f.write(soul_header + existing)

    # Upsert pricing skill (replaces template defaults with bidder-specific rates)
    pricing_dir = f"{profile_dir}/skills/bidder-pricing"
    os.makedirs(pricing_dir, exist_ok=True)
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
    with open(f"{pricing_dir}/SKILL.md", "w") as f:
        f.write(pricing_skill)

    # Upsert file management skill
    fm_dir = f"{profile_dir}/skills/file-mgmt"
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

    # Copy auth.json from parent (or template if parent missing)
    auth_src = f"{HERMES_HOME}/auth.json"
    auth_dst = f"{profile_dir}/auth.json"
    if os.path.exists(auth_src):
        _run(["cp", auth_src, auth_dst])
    elif os.path.exists(f"{template_dir}/auth.json"):
        _run(["cp", f"{template_dir}/auth.json", auth_dst])

    logger.info("Created profile %s for %s (trades: %s)", profile_name, company_name, trades)
    return {"profile_name": profile_name, "status": "created", "source": "template" if bidder_id != "velobid" else "fresh"}


class AdminHandler(BaseHTTPRequestHandler):
    def _json(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        if self.path == "/admin/health":
            self._json({"status": "ok"})
        elif self.path == "/admin/profiles":
            profiles_dir = f"{HERMES_HOME}/profiles"
            if os.path.isdir(profiles_dir):
                profiles = sorted(os.listdir(profiles_dir))
            else:
                profiles = []
            self._json({"profiles": profiles})
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
