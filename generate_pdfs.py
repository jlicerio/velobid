"""BidForge CLI — generate PDF documents from project + trade configs.

Usage:
    python generate_pdfs.py --project config/projects/shalom.json --trade hvac --output bid_projects/
    python generate_pdfs.py --project config/projects/shalom.json --trade hvac --template bid_proposal --output bid_projects/
    python generate_pdfs.py --project config/projects/shalom.json --trade hvac --all --output bid_projects/
"""

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

from bid_engine.models import Bid, Bidder, LineItem, PricingContext, Project, TradeConfig
from bid_engine.pricing_engine import PricingEngine
from bid_engine.templates.bid_proposal import BidProposalGenerator
from bid_engine.templates.bom_manpower import BOMManpowerGenerator
from bid_engine.templates.cost_summary import CostSummaryGenerator
from bid_engine.templates.full_scope import FullScopeGenerator
from bid_engine.templates.technical_scope import TechnicalScopeGenerator
from bid_engine.validators import BidValidator

TEMPLATES: dict[str, type] = {
    "bid_proposal": BidProposalGenerator,
    "full_scope": FullScopeGenerator,
    "bom_manpower": BOMManpowerGenerator,
    "cost_summary": CostSummaryGenerator,
    "technical_scope": TechnicalScopeGenerator,
}

TEMPLATE_PACKAGES: dict[str, list[str]] = {
    "all": list(TEMPLATES.keys()),
    "client": ["bid_proposal", "technical_scope", "full_scope"],
    "internal": ["full_scope", "bom_manpower", "cost_summary"],
}

TRADE_ALIASES: dict[str, str] = {
    "hvac": "hvac",
    "23": "hvac",
    "plumbing": "plumbing",
    "22": "plumbing",
    "electrical": "electrical",
    "26": "electrical",
}

BIDDER_ALIASES: dict[str, str] = {
    "air_hero": "air_hero",
    "hero": "air_hero",
}


def load_config(path: str) -> dict:
    """Load and parse a JSON config file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(p, encoding="utf-8-sig") as f:
        return json.load(f)


def resolve_bidder_path(bidder_ref: str | None = None) -> str:
    """Resolve bidder reference to full config path.

    Supports:
    - None or empty → defaults to "config/bidders/air_hero/bidder.json"
    - "air_hero" or "hero" → resolves via BIDDER_ALIASES
    - Full path like "config/bidders/custom/bidder.json" → returned as-is
    """
    if not bidder_ref or bidder_ref.strip() == "":
        bidder_ref = "air_hero"

    # Check if it's an alias
    bidder_key = BIDDER_ALIASES.get(bidder_ref.lower())
    if bidder_key:
        return f"config/bidders/{bidder_key}/bidder.json"

    # Check if it's already a full path
    if bidder_ref.startswith("config/") and bidder_ref.endswith(".json"):
        return bidder_ref

    # Otherwise treat it as a bidder directory name
    return f"config/bidders/{bidder_ref}/bidder.json"


def resolve_templates(template_name: str | None, package_name: str) -> list[str]:
    """Resolve the final template list from --template / --package flags.

    If --template is provided, it takes priority and package is ignored.
    """
    if template_name:
        return [template_name]

    package_key = (package_name or "all").lower()
    if package_key not in TEMPLATE_PACKAGES:
        raise ValueError(
            f"Unknown package '{package_name}'. Available: {list(TEMPLATE_PACKAGES.keys())}"
        )

    return TEMPLATE_PACKAGES[package_key]


def build_bid(
    project_config: dict,
    trade_config: dict,
    bidder_config: dict,
    region: str | None = None,
) -> Bid:
    """Construct a Bid object from parsed JSON configs."""
    project = Project.from_dict(project_config)
    bidder = Bidder.from_dict(bidder_config)
    trade = TradeConfig.from_dict(trade_config)
    region = region or trade.default_region

    bid_date_str = project_config.get("bid_date")
    bid_date = date.fromisoformat(bid_date_str) if bid_date_str else None

    contingency = project_config.get("pricing", {}).get("contingency_pct", 5.0)
    op_pct = project_config.get("pricing", {}).get("overhead_profit_pct", 15.0)

    # Get bid type from project config (default: ductwork_only)
    bid_type = project_config.get("bid_type", "ductwork_only")

    # Use project-level exclusions for turnkey or labor-only equipment bids
    if bid_type in ["turnkey", "labor_only_equipment"]:
        exclusions = list(project_config.get("technical_scope", {}).get("exclusions", []))
        if not exclusions:
            exclusions = list(trade.default_exclusions or [])
            # Remove the exclusion for equipment if it's labor-only-equipment (since we ARE providing labor)
            if bid_type == "labor_only_equipment":
                exclusions = [e for e in exclusions if "Supplying or setting" not in e]
                exclusions.append(
                    "Supplying of AHUs, Condensing Units, and Exhaust Fans is excluded (Owner Provided)"
                )
    else:
        exclusions = list(trade.default_exclusions or [])

    # O&P are visible internally but redacted in client packages via package_name
    bid = Bid(
        project=project,
        bidder=bidder,
        trade=trade,
        region=region,
        exclusions=exclusions,
        contingency_pct=contingency,
        overhead_profit_pct=op_pct,
        bid_date=bid_date,
    )

    # Build default line items from trade config (pass bid_type)
    line_items = _build_line_items_from_trade(trade, region, bid_type)
    bid.line_items = line_items

    # Price the bid
    context = PricingContext.from_trade_and_project(trade, project, region)
    engine = PricingEngine(context)
    bid = engine.price_bid(bid)
    bid = engine.apply_complexity_multipliers(bid)
    bid = engine.recalculate_totals(bid)

    return bid


def _build_line_items_from_trade(
    trade: TradeConfig, region: str, bid_type: str = "ductwork_only"
) -> list[LineItem]:
    """Build default line items from a trade config for demonstration.

    Args:
        trade: The trade configuration
        region: Region for labor rate lookup
        bid_type: "ductwork_only" or "turnkey" (includes equipment)

    In Phase 3+ this will be replaced by AI-generated takeoff items.
    """
    items: list[LineItem] = []
    labor_rate = trade.get_labor_rate(region)

    # HVAC default items (mirrors original bom.md)
    if trade.division == 23:
        items.extend(
            [
                LineItem(
                    cost_code="23-31-00",
                    description="Sheet Metal Fabrication (7,500 lbs)",
                    quantity=7500,
                    unit="lbs",
                    unit_cost_material=4.0,
                    labor_hours=300,
                    labor_factor="25 lbs/hr",
                    sort_order=1,
                ),
                LineItem(
                    cost_code="23-31-13",
                    description="Air Distribution & Flex Drops (40 ea)",
                    quantity=40,
                    unit="ea",
                    unit_cost_material=80.0,
                    labor_hours=20,
                    labor_factor="0.5 hrs/drop",
                    sort_order=2,
                ),
                LineItem(
                    cost_code="23-05-29",
                    description="Hangers, Supports & Seismic Bracing",
                    quantity=1,
                    unit="lot",
                    unit_cost_material=3800.0,
                    labor_hours=34,
                    labor_factor="34 hrs/lot",
                    sort_order=3,
                ),
                LineItem(
                    cost_code="23-07-13",
                    description="Duct Insulation & Seam Sealing",
                    quantity=1,
                    unit="lot",
                    unit_cost_material=4000.0,
                    labor_hours=64,
                    labor_factor="64 hrs/lot",
                    sort_order=4,
                ),
                LineItem(
                    cost_code="23-05-93",
                    description="Leak Testing & System Prep",
                    quantity=1,
                    unit="lot",
                    unit_cost_material=0.0,
                    labor_hours=24,
                    labor_factor="24 hrs total",
                    sort_order=5,
                ),
            ]
        )

        # Add equipment line items for turnkey or labor-only equipment bid scope
        if bid_type == "turnkey":
            items.extend(
                [
                    LineItem(
                        cost_code="23-81-00",
                        description="Air Handling Units (5x) - Supply & Installation",
                        quantity=5,
                        unit="ea",
                        unit_cost_material=5200.0,
                        labor_hours=100,
                        labor_factor="20 hrs/ea",
                        sort_order=6,
                    ),
                    LineItem(
                        cost_code="23-82-00",
                        description="Condensing Units (5x) - Supply & Installation",
                        quantity=5,
                        unit="ea",
                        unit_cost_material=6400.0,
                        labor_hours=80,
                        labor_factor="16 hrs/ea",
                        sort_order=7,
                    ),
                ]
            )
        elif bid_type == "labor_only_equipment":
            items.extend(
                [
                    LineItem(
                        cost_code="23-81-00",
                        description="Air Handling Units (5x) - Installation Only (Owner Provided)",
                        quantity=5,
                        unit="ea",
                        unit_cost_material=0.0,
                        labor_hours=40,
                        labor_factor="8 hrs/unit",
                        sort_order=6,
                    ),
                    LineItem(
                        cost_code="23-82-00",
                        description="Condensing Units (5x) - Installation Only (Owner Provided)",
                        quantity=5,
                        unit="ea",
                        unit_cost_material=0.0,
                        labor_hours=20,
                        labor_factor="4 hrs/unit",
                        sort_order=7,
                    ),
                ]
            )
    elif trade.division == 22:
        items.extend(
            [
                LineItem(
                    cost_code="22-10-00",
                    description="Plumbing Rough-in",
                    quantity=1,
                    unit="lot",
                    unit_cost_material=5000.0,
                    labor_hours=80,
                    labor_factor="80 hrs/lot",
                    sort_order=1,
                ),
                LineItem(
                    cost_code="22-30-00",
                    description="Plumbing Fixtures",
                    quantity=5,
                    unit="ea",
                    unit_cost_material=400.0,
                    labor_hours=20,
                    labor_factor="4 hrs/ea",
                    sort_order=2,
                ),
            ]
        )
    elif trade.division == 26:
        items.extend(
            [
                LineItem(
                    cost_code="26-05-00",
                    description="Electrical Rough-in",
                    quantity=1,
                    unit="lot",
                    unit_cost_material=8000.0,
                    labor_hours=120,
                    labor_factor="120 hrs/lot",
                    sort_order=1,
                ),
                LineItem(
                    cost_code="26-51-00",
                    description="Light Fixtures",
                    quantity=40,
                    unit="ea",
                    unit_cost_material=65.0,
                    labor_hours=40,
                    labor_factor="1 hr/ea",
                    sort_order=2,
                ),
            ]
        )

    # Compute labor costs from hours
    for li in items:
        li.unit_cost_labor = round((li.labor_hours * labor_rate) / max(li.quantity, 1), 2)

    return items


def generate(
    project_path: str,
    trade_name: str,
    output_dir: str,
    template_name: str | None = None,
    package_name: str = "all",
    region: str | None = None,
    validate: bool = True,
) -> list[str]:
    """Generate one or more PDFs based on config files.

    Returns a list of generated file paths.
    """
    trade_key = TRADE_ALIASES.get(trade_name.lower(), trade_name.lower())
    project_data = load_config(project_path)
    trade_data = load_config(f"config/trades/{trade_key}.json")

    bidder_ref = project_data.get("bidder", None)
    bidder_path = resolve_bidder_path(bidder_ref)
    bidder_data = load_config(bidder_path)

    bid = build_bid(project_data, trade_data, bidder_data, region)

    if validate:
        validator = BidValidator()
        result = validator.validate(bid)
        if not result.is_valid:
            print("WARNING: Bid validation errors:")
            for err in result.errors:
                print(f"  [{err.field}] {err.message}")
            print("Proceeding with generation anyway...")

    templates_to_run = resolve_templates(template_name, package_name)
    generated: list[str] = []

    for tpl_key in templates_to_run:
        if tpl_key not in TEMPLATES:
            print(f"ERROR: Unknown template '{tpl_key}'. Available: {list(TEMPLATES.keys())}")
            continue

        # Determine subfolder if package is provided
        current_output_dir = output_dir
        if package_name and package_name.lower() != "all":
            current_output_dir = os.path.join(output_dir, package_name.lower())

        generator_class = TEMPLATES[tpl_key]
        generator = generator_class(bid, output_dir=current_output_dir, package_name=package_name)
        out_path = generator.render()
        generated.append(out_path)
        print(f"Generated: {out_path}")

    return generated


def main() -> None:
    parser = argparse.ArgumentParser(description="BidForge PDF Generator")
    parser.add_argument(
        "--project",
        required=True,
        help="Path to project config JSON file",
    )
    parser.add_argument(
        "--trade",
        required=True,
        help="Trade name or division number (hvac, plumbing, electrical, or 22, 23, 26)",
    )
    parser.add_argument(
        "--template",
        default=None,
        help=f"Template to generate: {list(TEMPLATES.keys())}. Defaults to all.",
    )
    parser.add_argument(
        "--package",
        default="all",
        choices=list(TEMPLATE_PACKAGES.keys()),
        help="Template bundle: 'client' (submission-safe), 'internal' (ops-only), or 'all'.",
    )
    parser.add_argument(
        "--output",
        default="bid_projects",
        help="Output directory for generated PDFs. Defaults to 'bid_projects'.",
    )
    parser.add_argument(
        "--region",
        default=None,
        help="Region override for labor rates. Defaults to trade's default region.",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip bid validation before PDF generation.",
    )
    args = parser.parse_args()

    try:
        generated = generate(
            project_path=args.project,
            trade_name=args.trade,
            output_dir=args.output,
            template_name=args.template,
            package_name=args.package,
            region=args.region,
            validate=not args.skip_validation,
        )
        if not generated:
            print("No PDFs generated. Check template name and try again.")
            sys.exit(1)
        print(f"\nDone. {len(generated)} PDF(s) written to {args.output}/")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
