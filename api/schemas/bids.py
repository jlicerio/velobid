"""Pydantic schemas for bid API requests and responses."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ConfigSummary(BaseModel):
    """Small config descriptor used by UI dropdowns."""

    id: str
    name: str
    path: str


class GenerateBidRequest(BaseModel):
    """Inputs required to build a bid preview or PDF package."""

    model_config = ConfigDict(populate_by_name=True)

    project_id: str = Field(..., examples=["shalom_prayer_center"])
    trade: str = Field("hvac", examples=["hvac", "plumbing", "electrical"])
    template_name: str | None = Field(None, examples=["bid_proposal"])
    package_name: Literal["all", "client", "internal"] = "all"
    region: str | None = None
    run_validation: bool = Field(True, alias="validate")


class LineItemResponse(BaseModel):
    cost_code: str
    description: str
    quantity: float
    unit: str
    unit_cost_material: float
    unit_cost_labor: float
    total_material: float
    total_labor: float
    total_phase: float
    labor_hours: float
    labor_factor: str
    sort_order: int


class BidTotalsResponse(BaseModel):
    total_material: float
    total_labor: float
    total_direct_cost: float
    contingency: float
    overhead_profit: float
    total_bid_amount: float
    total_labor_hours: float
    contingency_pct: float
    overhead_profit_pct: float


class ValidationIssueResponse(BaseModel):
    field: str
    message: str


class BidPreviewResponse(BaseModel):
    project_name: str
    bidder_name: str
    trade_name: str
    region: str
    status: str
    totals: BidTotalsResponse
    line_items: list[LineItemResponse]
    exclusions: list[str]
    validation: list[ValidationIssueResponse]


class GeneratedFileResponse(BaseModel):
    filename: str
    path: str
    url: str


class GenerateBidResponse(BaseModel):
    preview: BidPreviewResponse
    generated_files: list[GeneratedFileResponse]


class ProjectPricingResponse(BaseModel):
    """Project listing with real pricing data."""

    id: str
    name: str
    total_bid: float = 0.0
    total_material: float = 0.0
    total_labor: float = 0.0
    total_labor_hours: float = 0.0
    trade: str = "hvac"
    version_count: int = 0
    area_sf: float | None = None
    status: str = "estimating"
    archived: bool = False
    city: str | None = None
    state: str | None = None


class CreateProjectRequest(BaseModel):
    """Request to create a new project."""

    name: str
    city: str | None = None
    state: str | None = None
    trade: str = "hvac"
    total_area_sf: float | None = None
    construction_type: str | None = None


class BulkArchiveRequest(BaseModel):
    """Request to archive or unarchive multiple projects at once."""

    ids: list[str] = Field(..., examples=[["shalom_prayer_center", "office_building_a"]])
    archived: bool = Field(..., examples=[True])
