"""Data models for BidForge — mirrors the database schema in-memory."""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass
class Project:
    """Represents a construction project."""

    name: str
    address: str
    city: str
    state: str
    zip_code: str
    total_area_sf: float
    occupancy_group: str = ""
    construction_type: str = ""
    max_height: str = ""
    design_group: str = ""
    structural_engineer: str = ""
    mep_engineer: str = ""
    governing_codes: dict[str, str] = field(default_factory=dict)
    site_data: dict[str, Any] = field(default_factory=dict)
    building_data: dict[str, Any] = field(default_factory=dict)
    owner: str = ""
    owner_contact: dict[str, str] = field(default_factory=dict)
    bid_date: date | None = None
    reference_sheets: dict[str, str] = field(default_factory=dict)
    technical_scope: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        """Construct a Project from a JSON dict."""
        governing = data.get("governing_codes", {})
        site = data.get("site_data", {})
        building = data.get("building_data", {})
        owner_contact = data.get("owner_contact", {})
        ref_sheets = data.get("reference_sheets", {})
        technical_scope = data.get("technical_scope", {})
        if not technical_scope:
            technical_scope = {}
            if "hvac_scope" in data:
                technical_scope["hvac_scope"] = data["hvac_scope"]
            if "electrical_scope" in data:
                technical_scope["electrical_scope"] = data["electrical_scope"]
            if "plumbing_scope" in data:
                technical_scope["plumbing_scope"] = data["plumbing_scope"]

        bid_date_str = data.get("bid_date")
        bid_date = date.fromisoformat(bid_date_str) if bid_date_str else None
        return cls(
            name=data["name"],
            address=data["address"],
            city=data["city"],
            state=data["state"],
            zip_code=data.get("zip_code", ""),
            total_area_sf=data.get("total_area_sf", 0.0),
            occupancy_group=data.get("occupancy_group", ""),
            construction_type=data.get("construction_type", ""),
            max_height=data.get("max_height", ""),
            design_group=data.get("design_group", ""),
            structural_engineer=data.get("structural_engineer", ""),
            mep_engineer=data.get("mep_engineer", ""),
            governing_codes=governing,
            site_data=site,
            building_data=building,
            owner=data.get("owner", ""),
            owner_contact=owner_contact,
            bid_date=bid_date,
            reference_sheets=ref_sheets,
            technical_scope=technical_scope,
        )


@dataclass
class Bidder:
    """Represents a company/bidder profile."""

    company_name: str
    primary_contact: str
    contact_email: str
    phone: str = ""
    location: str = ""
    trade_domain: str = ""
    operating_region: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "Bidder":
        return cls(
            company_name=data["company_name"],
            primary_contact=data["primary_contact"],
            contact_email=data["contact_email"],
            phone=data.get("phone", ""),
            location=data.get("location", ""),
            trade_domain=data.get("trade_domain", ""),
            operating_region=data.get("operating_region", ""),
        )


@dataclass
class TradeConfig:
    """Trade-specific configuration (labor rates, cost codes, compliance)."""

    division: int
    name: str
    full_name: str
    default_region: str
    labor_rates: dict[str, dict]
    compliance_codes: list[dict]
    cost_codes: list[dict]
    equipment_categories: list[str]
    labor_factors: dict[str, Any]
    material_rates: dict[str, Any]
    complexity_multipliers: list[dict]
    default_exclusions: list[str]
    templates: dict[str, Any]
    regional_adjustments: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict) -> "TradeConfig":
        return cls(
            division=data["division"],
            name=data["name"],
            full_name=data["full_name"],
            default_region=data.get("default_region", "National"),
            labor_rates=data.get("labor_rates", {}),
            compliance_codes=data.get("compliance_codes", []),
            cost_codes=data.get("cost_codes", []),
            equipment_categories=data.get("equipment_categories", []),
            labor_factors=data.get("labor_factors", {}),
            material_rates=data.get("material_rates", {}),
            complexity_multipliers=data.get("complexity_multipliers", []),
            default_exclusions=data.get("default_exclusions", []),
            templates=data.get("templates", {}),
            regional_adjustments=data.get("regional_adjustments", {}),
        )

    def get_labor_rate(self, region: str | None = None) -> float:
        """Return the burdened labor rate for a region."""
        region = region or self.default_region
        if region in self.labor_rates:
            return float(self.labor_rates[region]["burdened_rate"])
        rates = list(self.labor_rates.values())
        return float(rates[0]["burdened_rate"]) if rates else 0.0


@dataclass
class LineItem:
    """A single line item in a bid Schedule of Values."""

    cost_code: str
    description: str
    quantity: float
    unit: str
    unit_cost_material: float = 0.0
    unit_cost_labor: float = 0.0
    labor_hours: float = 0.0
    labor_factor: str = ""
    sort_order: int = 0
    id: str = ""

    @property
    def total_material(self) -> float:
        return round(self.quantity * self.unit_cost_material, 2)

    @property
    def total_labor(self) -> float:
        return round(self.quantity * self.unit_cost_labor, 2)

    @property
    def total_phase(self) -> float:
        return round(self.total_material + self.total_labor, 2)

    def to_dict(self) -> dict:
        return {
            "cost_code": self.cost_code,
            "description": self.description,
            "quantity": self.quantity,
            "unit": self.unit,
            "unit_cost_material": self.unit_cost_material,
            "unit_cost_labor": self.unit_cost_labor,
            "total_material": self.total_material,
            "total_labor": self.total_labor,
            "total_phase": self.total_phase,
            "labor_hours": self.labor_hours,
            "labor_factor": self.labor_factor,
            "sort_order": self.sort_order,
        }


@dataclass
class Bid:
    """Represents a complete bid with line items."""

    project: Project
    bidder: Bidder
    trade: TradeConfig
    region: str
    line_items: list[LineItem] = field(default_factory=list)
    exclusions: list[str] = field(default_factory=list)
    contingency_pct: float = 5.0
    overhead_profit_pct: float = 15.0
    bid_date: date | None = None
    version: int = 1
    status: str = "draft"

    @property
    def total_material(self) -> float:
        return round(sum(li.total_material for li in self.line_items), 2)

    @property
    def total_labor(self) -> float:
        return round(sum(li.total_labor for li in self.line_items), 2)

    @property
    def total_direct_cost(self) -> float:
        return round(self.total_material + self.total_labor, 2)

    @property
    def contingency_amount(self) -> float:
        return round(self.total_direct_cost * (self.contingency_pct / 100.0), 2)

    @property
    def overhead_profit_amount(self) -> float:
        pre_contingency = self.total_direct_cost + self.contingency_amount
        return round(pre_contingency * (self.overhead_profit_pct / 100.0), 2)

    @property
    def total_bid_amount(self) -> float:
        return round(
            self.total_direct_cost + self.contingency_amount + self.overhead_profit_amount,
            2,
        )

    @property
    def total_labor_hours(self) -> float:
        return round(sum(li.labor_hours for li in self.line_items), 1)

    def sov_summary(self) -> dict:
        """Return a flat dict of all SOV totals."""
        return {
            "total_material": self.total_material,
            "total_labor": self.total_labor,
            "total_direct_cost": self.total_direct_cost,
            "contingency": self.contingency_amount,
            "overhead_profit": self.overhead_profit_amount,
            "total_bid_amount": self.total_bid_amount,
            "total_labor_hours": self.total_labor_hours,
            "contingency_pct": self.contingency_pct,
            "overhead_profit_pct": self.overhead_profit_pct,
        }


@dataclass
class PricingContext:
    """Context for the pricing engine — trade, region, and project overrides."""

    trade: TradeConfig
    project: Project
    region: str
    labor_rate: float = 0.0
    contingency_pct: float = 5.0
    overhead_profit_pct: float = 15.0

    @classmethod
    def from_trade_and_project(
        cls, trade: TradeConfig, project: Project, region: str | None = None
    ) -> "PricingContext":
        region = region or trade.default_region
        labor_rate = trade.get_labor_rate(region)
        contingency = project.governing_codes.get("_contingency_pct", 5.0)
        op_pct = project.governing_codes.get("_op_pct", 15.0)
        return cls(
            trade=trade,
            project=project,
            region=region,
            labor_rate=labor_rate,
            contingency_pct=contingency,
            overhead_profit_pct=op_pct,
        )
