"""Profile management via Hermes container's internal admin API.

Uses HTTP instead of Docker exec to create bidder profiles,
making it compatible with both Docker and K8s deployments.
"""
import json
import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

ADMIN_URL = os.getenv("HERMES_ADMIN_URL", "http://hermes:8640")


def create_bidder_profile(
    bidder_id: str,
    company_name: str,
    trades: list[str],
    company_context: str = "",
    default_labor_rate: float = 65.0,
    default_equipment_markup_pct: float = 10.0,
    default_overhead_profit_pct: float = 15.0,
    default_contingency_pct: float = 5.0,
    default_tax_rate: float = 0.0825,
    service_area: str = "Nationwide",
) -> dict:
    """Create a Hermes profile via the admin HTTP API inside the Hermes container."""
    payload = {
        "bidder_id": bidder_id,
        "company_name": company_name,
        "trades": trades,
        "company_context": company_context,
        "service_area": service_area,
        "pricing": {
            "labor_rate": default_labor_rate,
            "equipment_markup_pct": default_equipment_markup_pct,
            "overhead_profit_pct": default_overhead_profit_pct,
            "contingency_pct": default_contingency_pct,
            "tax_rate": default_tax_rate,
        },
    }

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                f"{ADMIN_URL}/admin/profiles",
                json=payload,
            )
            resp.raise_for_status()
            result = resp.json()

        logger.info(
            "Created Hermes profile %s for %s",
            result.get("profile_name"),
            company_name,
        )
        return result

    except httpx.HTTPStatusError as e:
        detail = e.response.text[:200] if e.response else str(e)
        raise RuntimeError(f"Profile creation failed: {detail}")
    except httpx.RequestError as e:
        raise RuntimeError(
            f"Cannot reach Hermes admin API at {ADMIN_URL}: {e}"
        )
