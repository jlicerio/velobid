"""Flat-rate pricing engine for residential HVAC estimates."""

import json
from pathlib import Path
from typing import Optional


def load_trade_config() -> dict:
    """Load residential HVAC trade defaults."""
    config_path = Path(__file__).resolve().parents[2] / "config" / "trades" / "residential_hvac.json"
    with open(config_path, encoding="utf-8-sig") as f:
        return json.load(f)


def price_residential_estimate(
    equipment: list[dict],
    labor_tasks: list[dict],
    misc_materials: float = 0,
    permit_fee: Optional[float] = None,
    tax_rate: Optional[float] = None,
    equipment_markup_pct: Optional[float] = None,
    labor_rate: Optional[float] = None,
) -> dict:
    """Price a residential HVAC estimate using flat-rate model.

    Args:
        equipment: List of {item, cost, qty, brand, model, tons}
        labor_tasks: List of {item, hours, qty}
        misc_materials: Additional material cost
        permit_fee: Permit cost (override from config default)
        tax_rate: Sales tax rate (override)
        equipment_markup_pct: Markup % on equipment cost (override)
        labor_rate: Hourly labor rate (override)

    Returns:
        dict with line items and totals
    """
    config = load_trade_config()
    defaults = config["defaults"]

    eq_markup = equipment_markup_pct if equipment_markup_pct is not None else defaults["equipment_markup_pct"]
    lr = labor_rate if labor_rate is not None else defaults["labor_rate_per_hour"]
    pf = permit_fee if permit_fee is not None else defaults["permit_fee"]
    tr = tax_rate if tax_rate is not None else defaults["tax_rate"]

    # Equipment line items
    eq_lines = []
    eq_total_cost = 0
    for eq in equipment:
        cost = eq.get("cost", 0) * eq.get("qty", 1)
        markup = round(cost * eq_markup / 100, 2)
        total = round(cost + markup, 2)
        eq_total_cost += cost
        eq_lines.append({
            "type": "equipment",
            "description": f"{eq.get('qty', 1)}x {eq.get('item', 'Equipment')}",
            "detail": f"{eq.get('brand', '')} {eq.get('model', '')}".strip(),
            "cost": round(cost, 2),
            "markup": markup,
            "total": total,
        })

    # Labor line items
    labor_lines = []
    total_labor_hours = 0
    for task in labor_tasks:
        hours = task.get("hours", 0) * task.get("qty", 1)
        total = round(hours * lr, 2)
        total_labor_hours += hours
        labor_lines.append({
            "type": "labor",
            "description": task.get("item", "Labor"),
            "hours": hours,
            "rate": lr,
            "total": total,
        })

    # Summary
    equipment_total = round(sum(l["total"] for l in eq_lines), 2)
    labor_total = round(sum(l["total"] for l in labor_lines), 2)
    subtotal = round(equipment_total + labor_total + misc_materials, 2)
    tax = round(subtotal * tr, 2)
    grand_total = round(subtotal + tax + pf, 2)

    return {
        "project_type": "residential",
        "line_items": eq_lines + labor_lines + ([{
            "type": "material",
            "description": "Miscellaneous materials",
            "total": round(misc_materials, 2),
        }] if misc_materials else []) + ([{
            "type": "permit",
            "description": "Permit fee",
            "total": pf,
        }] if pf else []),
        "totals": {
            "equipment_total": equipment_total,
            "labor_total": labor_total,
            "labor_hours": total_labor_hours,
            "misc_materials": round(misc_materials, 2),
            "permit_fee": pf,
            "subtotal": subtotal,
            "tax": tax,
            "tax_rate": tr,
            "equipment_markup_pct": eq_markup,
            "labor_rate": lr,
            "grand_total": grand_total,
        },
    }
