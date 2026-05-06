"""Settings endpoints — GET/PATCH the global app settings."""

from fastapi import APIRouter

from api.services.settings import as_dict, save

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


@router.get("")
async def get_settings():
    """Return current settings (merged with builtin defaults)."""
    return as_dict()


@router.patch("")
async def patch_settings(body: dict):
    """Merge provided keys into settings and persist to disk.

    Send only the fields you want to change:
      { "company": { "name": "New Name" } }
    Unknown top-level keys are silently ignored.
    """
    fresh = save(body)
    return {
        "ok": True,
        "settings": {
            "company": {
                "name": fresh.company.name,
                "address": fresh.company.address,
                "phone": fresh.company.phone,
                "email": fresh.company.email,
                "license_number": fresh.company.license_number,
            },
            "pricing": {
                "default_contingency_pct": fresh.pricing.default_contingency_pct,
                "default_overhead_profit_pct": fresh.pricing.default_overhead_profit_pct,
                "default_equipment_markup_pct": fresh.pricing.default_equipment_markup_pct,
                "default_labor_rate": fresh.pricing.default_labor_rate,
                "default_tax_rate": fresh.pricing.default_tax_rate,
                "default_permit_fee": fresh.pricing.default_permit_fee,
                "default_misc_material_pct": fresh.pricing.default_misc_material_pct,
            },
            "agent": {
                "model": fresh.agent.model,
                "temperature": fresh.agent.temperature,
                "company_context": fresh.agent.company_context,
            },
        },
    }
