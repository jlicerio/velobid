"""Pydantic schemas for version snapshot system (Bid Git)."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from typing_extensions import Literal

from pydantic import BaseModel, Field


class CreateVersionRequest(BaseModel):
    """Request body for creating a new version snapshot."""

    trigger_source: Literal["user_edit", "ai_refine", "vision_import", "bulk_update"]
    commit_message: Optional[str] = None


class TotalsDiff(BaseModel):
    """Diff for a single totals field between two versions."""

    from_val: float = Field(..., alias="from")
    to: float
    delta: float
    delta_pct: float


class LineItemChange(BaseModel):
    """A field-level change in a line item between two versions."""

    cost_code: str
    description: str
    field: str
    from_val: Any = Field(..., alias="from")
    to: Any


class VersionDiff(BaseModel):
    """Full diff between two version snapshots."""

    diff_type: str = "version_diff"
    from_version: Optional[str] = None
    to_version: str
    totals_changed: Dict[str, TotalsDiff] = Field(default_factory=dict)
    line_items_changed: List[LineItemChange] = Field(default_factory=list)
    line_items_added: List[Dict[str, Any]] = Field(default_factory=list)
    line_items_removed: List[Dict[str, Any]] = Field(default_factory=list)
    summary: str = ""


class SnapshotData(BaseModel):
    """The full bid data stored in a version snapshot."""

    project_name: str
    trade_name: str
    totals: Dict[str, Any]
    line_items: List[Dict[str, Any]]
    exclusions: List[str]


class VersionMetadata(BaseModel):
    """Metadata entry stored in index.json for each version."""

    version_id: str
    timestamp: str
    commit_message: str
    trigger_source: str
    snapshot_summary: Optional[str] = None


class VersionSnapshot(BaseModel):
    """Full snapshot data stored in a version JSON file."""

    version_id: str
    timestamp: str
    commit_message: str
    trigger_source: str
    snapshot_data: SnapshotData
    diff_from_previous: Optional[VersionDiff] = None


class VersionListResponse(BaseModel):
    """Response for listing all versions of a project/trade."""

    project_id: str
    trade: str
    versions: List[VersionMetadata]


class VersionDetailResponse(BaseModel):
    """Response for a single version snapshot."""

    version_id: str
    timestamp: str
    commit_message: str
    trigger_source: str
    snapshot_data: SnapshotData
    diff_from_previous: Optional[VersionDiff] = None


class VersionDiffResponse(BaseModel):
    """Response for a diff between two versions."""

    diff: VersionDiff


class CreateVersionResponse(BaseModel):
    """Response after creating a new version snapshot."""

    version_id: str
    commit_message: str
    timestamp: str
    diff: Optional[VersionDiff] = None


class RestoreVersionResponse(BaseModel):
    """Response for a version restore operation."""

    version_id: str
    project_name: str
    trade_name: str
    totals: Dict[str, Any]
    line_items: List[Dict[str, Any]]
    exclusions: List[str]

