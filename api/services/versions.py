"""Service layer for version snapshot system (Bid Git)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from api.schemas.bids import BidPreviewResponse
from api.schemas.versions import (
    CreateVersionResponse,
    LineItemChange,
    RestoreVersionResponse,
    SnapshotData,
    TotalsDiff,
    VersionDiff,
    VersionMetadata,
    VersionSnapshot,
)
from api.services.bids import OUTPUT_DIR


def _versions_dir(project_id: str, trade: str) -> Path:
    """Return the version directory for a project/trade pair."""
    return OUTPUT_DIR / project_id / trade / "versions"


def _index_path(project_id: str, trade: str) -> Path:
    """Return the path to index.json for a project/trade."""
    return _versions_dir(project_id, trade) / "index.json"


def _snapshot_path(project_id: str, trade: str, version_id: str) -> Path:
    """Return the path to a specific version snapshot JSON file."""
    return _versions_dir(project_id, trade) / f"{version_id}.json"


def _next_version_id(project_id: str, trade: str) -> str:
    """Determine the next version ID (v001, v002, ...)."""
    existing = _load_index(project_id, trade)
    if not existing:
        return "v001"
    last_id = existing[-1]["version_id"]
    try:
        num = int(last_id.lstrip("v")) + 1
    except (ValueError, IndexError):
        num = len(existing) + 1
    return f"v{num:03d}"


def _load_index(project_id: str, trade: str) -> List[Dict[str, Any]]:
    """Load the index.json for a project/trade, returning an empty list if missing."""
    path = _index_path(project_id, trade)
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig") as f:
        return json.load(f)


def _save_index(project_id: str, trade: str, index: List[Dict[str, Any]]) -> None:
    """Write the index.json for a project/trade."""
    path = _index_path(project_id, trade)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)


def _read_snapshot_file(project_id: str, trade: str, version_id: str) -> Dict[str, Any]:
    """Read a version snapshot JSON file."""
    path = _snapshot_path(project_id, trade, version_id)
    if not path.exists():
        raise FileNotFoundError(f"Version snapshot not found: {version_id}")
    with path.open(encoding="utf-8-sig") as f:
        return json.load(f)


def _write_snapshot_file(
    project_id: str, trade: str, version_id: str, data: Dict[str, Any]
) -> None:
    """Write a version snapshot JSON file."""
    path = _snapshot_path(project_id, trade, version_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def list_versions(project_id: str, trade: str) -> List[VersionMetadata]:
    """Return all version metadata entries for a project/trade."""
    entries = _load_index(project_id, trade)
    return [VersionMetadata(**entry) for entry in entries]


def get_snapshot(project_id: str, trade: str, version_id: str) -> VersionSnapshot:
    """Return a full version snapshot."""
    data = _read_snapshot_file(project_id, trade, version_id)
    return VersionSnapshot(**data)


def get_diff(project_id: str, trade: str, version_id: str) -> Optional[VersionDiff]:
    """Return the diff stored within a snapshot (comparing to previous)."""
    snapshot = get_snapshot(project_id, trade, version_id)
    return snapshot.diff_from_previous


def compute_diff(
    prev_snapshot: Dict[str, Any],
    curr_snapshot: Dict[str, Any],
    prev_version_id: Optional[str],
    curr_version_id: str,
) -> VersionDiff:
    """Compute a field-level diff between two snapshot data dicts.

    Compares:
      - totals (all float fields)
      - line items (by cost_code matching)
      - added/removed line items
    """
    prev_data = prev_snapshot.get("snapshot_data", {})
    curr_data = curr_snapshot.get("snapshot_data", {})

    prev_totals = prev_data.get("totals", {})
    curr_totals = curr_data.get("totals", {})

    prev_items = prev_data.get("line_items", [])
    curr_items = curr_data.get("line_items", [])

    # --- Totals diff ---
    totals_changed: Dict[str, TotalsDiff] = {}
    all_total_keys = set(list(prev_totals.keys()) + list(curr_totals.keys()))
    for key in sorted(all_total_keys):
        pv = prev_totals.get(key)
        cv = curr_totals.get(key)
        if pv == cv:
            continue
        if isinstance(pv, (int, float)) and isinstance(cv, (int, float)):
            delta = cv - pv
            delta_pct = round((delta / pv * 100) if pv else 0.0, 2)
            totals_changed[key] = TotalsDiff(
                from_val=pv, to=cv, delta=round(delta, 2), delta_pct=delta_pct
            )

    # --- Line items diff ---
    prev_by_code = {item.get("cost_code", ""): item for item in prev_items}
    curr_by_code = {item.get("cost_code", ""): item for item in curr_items}

    prev_codes = set(prev_by_code.keys())
    curr_codes = set(curr_by_code.keys())

    common_codes = prev_codes & curr_codes
    added_codes = curr_codes - prev_codes
    removed_codes = prev_codes - curr_codes

    line_items_changed: List[LineItemChange] = []
    for code in sorted(common_codes):
        p_item = prev_by_code[code]
        c_item = curr_by_code[code]
        changes = _compare_line_item_fields(p_item, c_item)
        line_items_changed.extend(changes)

    line_items_added: List[Dict[str, Any]] = [
        curr_by_code[code] for code in sorted(added_codes)
    ]
    line_items_removed: List[Dict[str, Any]] = [
        prev_by_code[code] for code in sorted(removed_codes)
    ]

    # --- Summary ---
    summary = _generate_summary(
        totals_changed,
        line_items_changed,
        line_items_added,
        line_items_removed,
        prev_totals,
        curr_totals,
    )

    return VersionDiff(
        diff_type="version_diff",
        from_version=prev_version_id,
        to_version=curr_version_id,
        totals_changed=totals_changed,
        line_items_changed=line_items_changed,
        line_items_added=line_items_added,
        line_items_removed=line_items_removed,
        summary=summary,
    )


_LINE_ITEM_FIELDS = [
    "quantity",
    "unit_cost_material",
    "unit_cost_labor",
    "total_material",
    "total_labor",
    "total_phase",
    "labor_hours",
    "labor_factor",
]


def _compare_line_item_fields(
    prev: Dict[str, Any], curr: Dict[str, Any]
) -> List[LineItemChange]:
    """Compare two line item dicts field by field, returning changes."""
    changes: List[LineItemChange] = []
    cost_code = prev.get("cost_code", curr.get("cost_code", ""))
    description = prev.get("description", curr.get("description", ""))
    for field in _LINE_ITEM_FIELDS:
        pv = prev.get(field)
        cv = curr.get(field)
        if pv != cv:
            changes.append(
                LineItemChange(
                    cost_code=cost_code,
                    description=description,
                    field=field,
                    from_val=pv,
                    to=cv,
                )
            )
    return changes


def _format_dollar(val: float) -> str:
    """Format a dollar amount (e.g., '$1,234.56')."""
    if val >= 0:
        return f"${val:,.2f}"
    return f"-${abs(val):,.2f}"


def _generate_summary(
    totals_changed: Dict[str, TotalsDiff],
    line_items_changed: List[LineItemChange],
    line_items_added: List[Dict[str, Any]],
    line_items_removed: List[Dict[str, Any]],
    prev_totals: Dict[str, Any],
    curr_totals: Dict[str, Any],
) -> str:
    """Generate a human-readable diff summary."""
    parts: List[str] = []

    if "total_bid_amount" in totals_changed:
        td = totals_changed["total_bid_amount"]
        direction = "increased" if td.delta >= 0 else "decreased"
        parts.append(
            f"Total bid {direction} by {_format_dollar(abs(td.delta))} ({td.delta_pct:+.2f}%)"
        )
    elif prev_totals.get("total_bid_amount") is not None:
        parts.append(
            f"Total bid unchanged at {_format_dollar(curr_totals.get('total_bid_amount', 0))}"
        )

    for key, td in totals_changed.items():
        if key == "total_bid_amount":
            continue
        nice_key = key.replace("_", " ").title()
        direction = "increased" if td.delta >= 0 else "decreased"
        parts.append(
            f"{nice_key} {direction} by {_format_dollar(abs(td.delta))} ({td.delta_pct:+.2f}%)"
        )

    if line_items_changed:
        changed_codes = list(set(c.cost_code for c in line_items_changed))
        parts.append(
            f"Changes in {len(line_items_changed)} field(s) across {len(changed_codes)} line item(s)"
        )

    if line_items_added:
        parts.append(f"{len(line_items_added)} line item(s) added")

    if line_items_removed:
        parts.append(f"{len(line_items_removed)} line item(s) removed")

    if not parts:
        return "No changes detected."

    return ". ".join(parts) + "."


def _serialize_bid_to_snapshot_data(bid_preview: BidPreviewResponse) -> SnapshotData:
    """Convert a BidPreviewResponse into serializable snapshot data."""
    return SnapshotData(
        project_name=bid_preview.project_name,
        trade_name=bid_preview.trade_name,
        totals=bid_preview.totals.model_dump(),
        line_items=[item.model_dump() for item in bid_preview.line_items],
        exclusions=bid_preview.exclusions,
    )


def _make_commit_message(
    trigger_source: str,
    snapshot_data: SnapshotData,
    diff: Optional[VersionDiff],
) -> str:
    """Generate a commit message based on the trigger source and diff."""
    if diff and diff.summary and diff.summary != "No changes detected.":
        return f"[{trigger_source}] {diff.summary}"
    return (
        f"[{trigger_source}] Initial snapshot -- "
        f"{snapshot_data.project_name} / {snapshot_data.trade_name}"
    )


def _make_snapshot_summary(snapshot_data: SnapshotData) -> str:
    """Generate a one-line summary for the index entry."""
    totals = snapshot_data.totals
    total_amount = totals.get("total_bid_amount", 0)
    labor_hours = totals.get("total_labor_hours", 0)
    return f"{_format_dollar(total_amount)} -- {labor_hours:.1f} hrs"


def create_snapshot(
    project_id: str,
    trade: str,
    trigger_source: str,
    bid_preview: BidPreviewResponse,
    commit_message: Optional[str] = None,
) -> CreateVersionResponse:
    """Create a new version snapshot from the current bid preview state."""
    snapshot_data = _serialize_bid_to_snapshot_data(bid_preview)
    version_id = _next_version_id(project_id, trade)

    entries = _load_index(project_id, trade)
    prev_version_id = entries[-1]["version_id"] if entries else None
    prev_data = None
    if prev_version_id:
        try:
            prev_data = _read_snapshot_file(project_id, trade, prev_version_id)
        except FileNotFoundError:
            prev_data = None

    diff = None
    if prev_data:
        curr_snapshot_for_diff = {
            "snapshot_data": snapshot_data.model_dump(),
        }
        diff = compute_diff(
            prev_data, curr_snapshot_for_diff, prev_version_id, version_id
        )

    if not commit_message:
        commit_message = _make_commit_message(trigger_source, snapshot_data, diff)

    timestamp = datetime.now(timezone.utc).isoformat()
    snapshot_summary = _make_snapshot_summary(snapshot_data)

    snapshot = VersionSnapshot(
        version_id=version_id,
        timestamp=timestamp,
        commit_message=commit_message,
        trigger_source=trigger_source,
        snapshot_data=snapshot_data,
        diff_from_previous=diff,
    )

    _write_snapshot_file(project_id, trade, version_id, snapshot.model_dump())

    metadata_entry = {
        "version_id": version_id,
        "timestamp": timestamp,
        "commit_message": commit_message,
        "trigger_source": trigger_source,
        "snapshot_summary": snapshot_summary,
    }
    entries.append(metadata_entry)
    _save_index(project_id, trade, entries)

    return CreateVersionResponse(
        version_id=version_id,
        commit_message=commit_message,
        timestamp=timestamp,
        diff=diff,
    )


def restore_snapshot(
    project_id: str, trade: str, version_id: str
) -> RestoreVersionResponse:
    """Restore a version snapshot, returning the bid data it contains."""
    snapshot = get_snapshot(project_id, trade, version_id)
    data = snapshot.snapshot_data
    return RestoreVersionResponse(
        version_id=version_id,
        project_name=data.project_name,
        trade_name=data.trade_name,
        totals=data.totals,
        line_items=data.line_items,
        exclusions=data.exclusions,
    )
