"""Service layer that adapts existing bid generation logic for HTTP/UI use."""

from __future__ import annotations

import json
import os
import re
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from api.schemas.bids import (
    BidPreviewResponse,
    BidTotalsResponse,
    ConfigSummary,
    CreateProjectRequest,
    GenerateBidRequest,
    GenerateBidResponse,
    GeneratedFileResponse,
    LineItemResponse,
    ProjectPricingResponse,
    ValidationIssueResponse,
)
from bid_engine.models import Bid
from bid_engine.validators import BidValidator
from generate_pdfs import build_bid, generate, resolve_bidder_path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
PROJECTS_DIR = CONFIG_DIR / "projects"
TRADES_DIR = CONFIG_DIR / "trades"
BID_PROJECTS_DIR = PROJECT_ROOT / "bid_projects"
OUTPUT_DIR = BID_PROJECTS_DIR / "api_generated"


@contextmanager
def project_cwd() -> Iterator[None]:
    """Run legacy relative-path code from the project root without changing callers."""
    previous = Path.cwd()
    os.chdir(PROJECT_ROOT)
    try:
        yield
    finally:
        os.chdir(previous)


def read_json(path: Path) -> dict:
    """Read a JSON file using UTF-8 with BOM tolerance."""
    with path.open(encoding="utf-8-sig") as file:
        return json.load(file)


def list_project_configs(show_archived: bool = False) -> list[ConfigSummary]:
    """Return available project JSON files for UI selection."""
    result = []
    for path in sorted(PROJECTS_DIR.glob("*.json")):
        if show_archived:
            result.append(_summary_from_json_file(path))
        else:
            data = read_json(path)
            if not data.get("archived", False):
                result.append(_summary_from_json_file(path))
    return result


def list_trade_configs() -> list[ConfigSummary]:
    """Return available trade JSON files for UI selection."""
    return [_summary_from_json_file(path) for path in sorted(TRADES_DIR.glob("*.json"))]


def build_bid_for_request(request: GenerateBidRequest) -> Bid:
    """Build a priced Bid object from a UI/API request."""
    project_path = resolve_project_path(request.project_id)
    trade_path = resolve_trade_path(request.trade)

    project_data = read_json(project_path)
    trade_data = read_json(trade_path)

    with project_cwd():
        bidder_path = PROJECT_ROOT / resolve_bidder_path(project_data.get("bidder"))
        bidder_data = read_json(bidder_path)
        return build_bid(
            project_config=project_data,
            trade_config=trade_data,
            bidder_config=bidder_data,
            region=request.region,
        )


def preview_bid(request: GenerateBidRequest) -> BidPreviewResponse:
    """Build a bid and return UI-friendly summary data without rendering PDFs."""
    bid = build_bid_for_request(request)
    return serialize_bid_preview(bid, validate=request.run_validation)


def generate_bid_files(request: GenerateBidRequest) -> GenerateBidResponse:
    """Generate PDFs through the existing generator and return links for the UI."""
    project_path = resolve_project_path(request.project_id)
    request_output_dir = OUTPUT_DIR / request.project_id / request.trade
    request_output_dir.mkdir(parents=True, exist_ok=True)

    with project_cwd():
        generated = generate(
            project_path=str(project_path.relative_to(PROJECT_ROOT)),
            trade_name=request.trade,
            output_dir=str(request_output_dir.relative_to(PROJECT_ROOT)),
            template_name=request.template_name,
            package_name=request.package_name,
            region=request.region,
            validate=request.run_validation,
        )

    preview = preview_bid(request)
    files = [serialize_generated_file(Path(path)) for path in generated]
    return GenerateBidResponse(preview=preview, generated_files=files)


def resolve_project_path(project_id: str) -> Path:
    """Resolve a safe project ID or file stem to a config path."""
    clean_id = Path(project_id).stem
    path = PROJECTS_DIR / f"{clean_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Project config not found: {clean_id}")
    return path


def resolve_trade_path(trade: str) -> Path:
    """Resolve a safe trade ID or file stem to a config path."""
    aliases = {"23": "hvac", "22": "plumbing", "26": "electrical"}
    clean_trade = aliases.get(trade.lower(), Path(trade).stem.lower())
    path = TRADES_DIR / f"{clean_trade}.json"
    if not path.exists():
        raise FileNotFoundError(f"Trade config not found: {clean_trade}")
    return path


def serialize_bid_preview(bid: Bid, validate: bool = True) -> BidPreviewResponse:
    """Convert a Bid dataclass into an API response model."""
    validation = BidValidator.validate(bid).errors if validate else []
    return BidPreviewResponse(
        project_name=bid.project.name,
        bidder_name=bid.bidder.company_name,
        trade_name=bid.trade.name,
        region=bid.region,
        status=bid.status,
        totals=BidTotalsResponse(**bid.sov_summary()),
        line_items=[LineItemResponse(**line_item.to_dict()) for line_item in bid.line_items],
        exclusions=bid.exclusions,
        validation=[
            ValidationIssueResponse(field=issue.field, message=issue.message)
            for issue in validation
        ],
    )


def serialize_generated_file(path: Path) -> GeneratedFileResponse:
    """Convert a generated file path into a safe static-download URL."""
    resolved = path.resolve()
    relative = resolved.relative_to(BID_PROJECTS_DIR)
    return GeneratedFileResponse(
        filename=resolved.name,
        path=str(relative).replace("\\", "/"),
        url=f"/files/{relative.as_posix()}",
    )


def _summary_from_json_file(path: Path) -> ConfigSummary:
    data = read_json(path)
    return ConfigSummary(
        id=path.stem,
        name=data.get("full_name") or data.get("name") or path.stem.replace("_", " ").title(),
        path=str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
    )


# ---------------------------------------------------------------------------
# Module-level cache for list_projects_with_pricing
# ---------------------------------------------------------------------------
_pricing_cache: dict = {}
_PRICING_CACHE_TTL = 30  # seconds


def list_projects_with_pricing() -> list[ProjectPricingResponse]:
    """Return every project with real pricing from preview_bid()."""
    now = time.time()
    cache_key = "list_projects_with_pricing"
    cached = _pricing_cache.get(cache_key)
    if cached and (now - cached["ts"]) < _PRICING_CACHE_TTL:
        return cached["data"]

    results: list[ProjectPricingResponse] = []
    for path in sorted(PROJECTS_DIR.glob("*.json")):
        project_id = path.stem
        project_data = read_json(path)

        name = project_data.get("name") or project_id.replace("_", " ").title()
        city = project_data.get("city")
        state = project_data.get("state")
        area_sf = project_data.get("total_area_sf")
        archived = project_data.get("archived", False)

        # Count versions from OUTPUT_DIR/project_id/hvac/versions/index.json
        versions_path = OUTPUT_DIR / project_id / "hvac" / "versions" / "index.json"
        version_count = 0
        if versions_path.exists():
            try:
                version_index = read_json(versions_path)
                version_count = len(version_index) if isinstance(version_index, list) else 0
            except Exception:
                version_count = 0

        # Compute pricing via preview_bid()
        total_bid = 0.0
        total_material = 0.0
        total_labor = 0.0
        try:
            req = GenerateBidRequest(project_id=project_id, trade="hvac", run_validation=False)
            preview = preview_bid(req)
            total_bid = preview.totals.total_bid_amount
            total_material = preview.totals.total_material
            total_labor = preview.totals.total_labor
        except Exception:
            pass

        results.append(
            ProjectPricingResponse(
                id=project_id,
                name=name,
                total_bid=total_bid,
                total_material=total_material,
                total_labor=total_labor,
                trade="hvac",
                version_count=version_count,
                area_sf=area_sf,
                archived=archived,
                city=city,
                state=state,
            )
        )

    _pricing_cache[cache_key] = {"data": results, "ts": now}
    return results


def _project_id_from_name(name: str) -> str:
    """Convert a project name to a snake_case project ID."""
    return re.sub(r"[^a-z0-9_]", "", name.lower().replace(" ", "_"))


def create_project(request: CreateProjectRequest) -> ProjectPricingResponse:
    """Create a new project config and return its pricing summary."""
    project_id = _project_id_from_name(request.name)

    # Read the default trade config for pricing defaults
    trade_path = resolve_trade_path(request.trade)
    trade_data = read_json(trade_path)

    project_path = PROJECTS_DIR / f"{project_id}.json"
    if project_path.exists():
        raise FileExistsError(f"Project already exists: {project_id}")

    project_config = {
        "name": request.name,
        "city": request.city,
        "state": request.state,
        "trade": request.trade,
        "total_area_sf": request.total_area_sf,
        "construction_type": request.construction_type,
        "pricing": {
            "contingency_pct": trade_data.get("contingency_pct", 5.0),
            "overhead_profit_pct": trade_data.get("overhead_profit_pct", 15.0),
        },
        "archived": False,
    }

    project_path.parent.mkdir(parents=True, exist_ok=True)
    with project_path.open("w", encoding="utf-8") as f:
        json.dump(project_config, f, indent=2)

    return ProjectPricingResponse(
        id=project_id,
        name=request.name,
        trade=request.trade,
        area_sf=request.total_area_sf,
        archived=False,
        city=request.city,
        state=request.state,
    )


def archive_project(project_id: str, archived: bool = True) -> dict:
    """Set the archived flag on a project config file."""
    project_path = resolve_project_path(project_id)
    data = read_json(project_path)
    data["archived"] = archived
    with project_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    status = "archived" if archived else "unarchived"
    return {"message": f"Project '{project_id}' {status} successfully", "archived": archived}
