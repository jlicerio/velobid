"""Global Velobid settings — single JSON source of truth.

Pattern:
  settings = Settings()          # singleton, lazy-loaded
  settings.company.name           # "Air Hero LLC"
  settings.pricing.default_contingency_pct  # 5.0

Editable via API (PATCH /api/v1/settings) or direct disk edit.
Reloads on save. Never raises on missing file — uses hardcoded fallbacks.
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ── path resolution (same as bids.py) ──────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SETTINGS_PATH = PROJECT_ROOT / "config" / "settings.json"

# ── typed data classes ─────────────────────────────────────────────────────


@dataclass
class CompanySettings:
    name: str = "Air Hero LLC"
    address: str = ""
    phone: str = ""
    email: str = ""
    license_number: str = ""


@dataclass
class PricingSettings:
    default_contingency_pct: float = 5.0
    default_overhead_profit_pct: float = 15.0
    default_equipment_markup_pct: float = 25.0
    default_labor_rate: float = 95.0
    default_tax_rate: float = 0.0825
    default_permit_fee: float = 150.0
    default_misc_material_pct: float = 5.0


@dataclass
class AgentSettings:
    model: str = "air-hero"
    temperature: float = 0.3
    company_context: str = (
        "You are the AI project manager for Air Hero LLC. "
        "Be thorough and descriptive — when presenting data, include both "
        "readable sentences and supporting tables. Always lead with a sentence "
        "summary before any structured data."
    )


@dataclass
class Settings:
    company: CompanySettings = field(default_factory=CompanySettings)
    pricing: PricingSettings = field(default_factory=PricingSettings)
    agent: AgentSettings = field(default_factory=AgentSettings)


# ── loader with inline defaults ────────────────────────────────────────────

_BUILTIN = {
    "company": {
        "name": "Air Hero LLC",
        "address": "",
        "phone": "",
        "email": "",
        "license_number": "",
    },
    "pricing": {
        "default_contingency_pct": 5.0,
        "default_overhead_profit_pct": 15.0,
        "default_equipment_markup_pct": 25.0,
        "default_labor_rate": 95.0,
        "default_tax_rate": 0.0825,
        "default_permit_fee": 150.0,
        "default_misc_material_pct": 5.0,
    },
    "agent": {
        "model": "air-hero",
        "temperature": 0.3,
        "company_context": (
            "You are the AI project manager for Air Hero LLC. "
            "Be thorough and descriptive — when presenting data, include both "
            "readable sentences and supporting tables. Always lead with a sentence "
            "summary before any structured data."
        ),
    },
}


def _deep_merge(base: dict, overlay: dict) -> dict:
    """Merge *overlay* into *base* mutating base, preserving unknown keys."""
    for key, val in overlay.items():
        if key in base and isinstance(base[key], dict) and isinstance(val, dict):
            _deep_merge(base[key], val)
        elif key in base:
            base[key] = val
        # ignore unknown top-level keys so old settings files don't break on schema changes
    return base


def _dict_to_settings(raw: dict) -> Settings:
    c = raw.get("company", {})
    p = raw.get("pricing", {})
    a = raw.get("agent", {})
    return Settings(
        company=CompanySettings(**{f.name: c.get(f.name, f.default) for f in CompanySettings.__dataclass_fields__.values() if f.name != "get"}),
        pricing=PricingSettings(**{f.name: p.get(f.name, f.default) for f in PricingSettings.__dataclass_fields__.values() if f.name != "get"}),
        agent=AgentSettings(**{f.name: a.get(f.name, f.default) for f in AgentSettings.__dataclass_fields__.values() if f.name != "get"}),
    )


def _settings_to_dict(s: Settings) -> dict:
    return {
        "company": {f.name: getattr(s.company, f.name) for f in CompanySettings.__dataclass_fields__.values() if f.name != "get"},
        "pricing": {f.name: getattr(s.pricing, f.name) for f in PricingSettings.__dataclass_fields__.values() if f.name != "get"},
        "agent": {f.name: getattr(s.agent, f.name) for f in AgentSettings.__dataclass_fields__.values() if f.name != "get"},
    }


# ── singleton with thread-safe reload ──────────────────────────────────────

_lock = threading.Lock()
_cache: Settings | None = None


def load() -> Settings:
    """Get current settings (cached, lazy-loaded). Thread-safe."""
    global _cache
    if _cache is not None:
        return _cache

    with _lock:
        if _cache is not None:
            return _cache
        _cache = _load_from_disk()
        return _cache


def reload() -> Settings:
    """Force-reload from disk. Returns fresh Settings."""
    global _cache
    with _lock:
        _cache = _load_from_disk()
        return _cache


def _load_from_disk() -> Settings:
    if not SETTINGS_PATH.exists():
        return _dict_to_settings(dict(_BUILTIN))  # shallow copy
    try:
        raw = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        merged = _deep_merge(dict(_BUILTIN), raw)
        return _dict_to_settings(merged)
    except (json.JSONDecodeError, OSError) as exc:
        import logging
        logging.getLogger("settings").warning(
            "Failed to load %s: %s. Using defaults.", SETTINGS_PATH, exc
        )
        return _dict_to_settings(dict(_BUILTIN))


def save(raw: dict) -> Settings:
    """Write new settings dict to disk, merge with builtins, return fresh Settings."""
    merged = _deep_merge(dict(_BUILTIN), raw)
    SETTINGS_PATH.write_text(
        json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return reload()


def as_dict() -> dict:
    """Return current settings as a plain dict (safe for JSON serialization)."""
    return _settings_to_dict(load())
