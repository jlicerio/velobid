"""API routes for version snapshot system (Bid Git)."""

from fastapi import APIRouter, HTTPException

from api.schemas.bids import GenerateBidRequest
from api.schemas.versions import (
    CreateVersionRequest,
    CreateVersionResponse,
    RestoreVersionResponse,
    VersionDetailResponse,
    VersionDiffResponse,
    VersionListResponse,
)
from api.services.bids import preview_bid
from api.services.versions import (
    create_snapshot,
    get_diff,
    get_snapshot,
    list_versions,
    restore_snapshot,
)

router = APIRouter(prefix="/api/v1", tags=["versions"])


@router.get(
    "/bids/{project_id}/{trade}/versions",
    response_model=VersionListResponse,
)
def get_versions(project_id: str, trade: str) -> VersionListResponse:
    """List all version snapshots for a project/trade."""
    try:
        versions = list_versions(project_id, trade)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return VersionListResponse(
        project_id=project_id,
        trade=trade,
        versions=versions,
    )


@router.get(
    "/bids/{project_id}/{trade}/versions/{v}",
    response_model=VersionDetailResponse,
)
def get_version(project_id: str, trade: str, v: str) -> VersionDetailResponse:
    """Get a specific version snapshot."""
    try:
        snapshot = get_snapshot(project_id, trade, v)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return VersionDetailResponse(
        version_id=snapshot.version_id,
        timestamp=snapshot.timestamp,
        commit_message=snapshot.commit_message,
        trigger_source=snapshot.trigger_source,
        snapshot_data=snapshot.snapshot_data,
        diff_from_previous=snapshot.diff_from_previous,
    )


@router.get(
    "/bids/{project_id}/{trade}/versions/{v}/diff",
    response_model=VersionDiffResponse,
)
def get_version_diff(project_id: str, trade: str, v: str) -> VersionDiffResponse:
    """Get the diff from the previous version to this version."""
    try:
        diff = get_diff(project_id, trade, v)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    if diff is None:
        return VersionDiffResponse(diff=None)
    return VersionDiffResponse(diff=diff)


@router.post(
    "/bids/{project_id}/{trade}/versions",
    response_model=CreateVersionResponse,
    status_code=201,
)
def create_new_version(
    project_id: str,
    trade: str,
    request: CreateVersionRequest,
) -> CreateVersionResponse:
    """Create a new version snapshot from the current bid state."""
    try:
        bid_request = GenerateBidRequest(project_id=project_id, trade=trade)
        preview = preview_bid(bid_request)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    try:
        result = create_snapshot(
            project_id=project_id,
            trade=trade,
            trigger_source=request.trigger_source,
            bid_preview=preview,
            commit_message=request.commit_message,
        )
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    return result


@router.post(
    "/bids/{project_id}/{trade}/versions/{v}/restore",
    response_model=RestoreVersionResponse,
)
def restore_version(
    project_id: str,
    trade: str,
    v: str,
) -> RestoreVersionResponse:
    """Restore a version snapshot as the current active bid."""
    try:
        result = restore_snapshot(project_id, trade, v)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    return result
