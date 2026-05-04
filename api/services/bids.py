"""Service layer that adapts existing bid generation logic for HTTP/UI use."""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from api.schemas.bids import (
    BidPreviewResponse,
    BidTotalsResponse,
    ConfigSummary,
    GenerateBidRequest,
    GenerateBidResponse,
    GeneratedFileResponse,
    LineItemResponse,
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


def list_project_configs() -> list[ConfigSummary]:
    """Return available project JSON files for UI selection."""
    return [_summary_from_json_file(path) for path in sorted(PROJECTS_DIR.glob("*.json"))]


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
