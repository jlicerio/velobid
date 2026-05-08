"""Bid API routes for UI integration."""

import csv
import io
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, StreamingResponse

from api.schemas.bids import (
    BidPreviewResponse,
    BulkArchiveRequest,
    ConfigSummary,
    CreateProjectRequest,
    GenerateBidRequest,
    GenerateBidResponse,
    ProjectPricingResponse,
)
from api.services.bids import (
    BID_PROJECTS_DIR,
    archive_project,
    bulk_archive_project,
    create_project,
    generate_bid_files,
    list_project_configs,
    list_projects_with_pricing,
    list_trade_configs,
    project_status_label,
    preview_bid,
    resolve_project_path,
)
from api.services.auth_guard import AuthContext, get_auth_context, parse_auth_context

router = APIRouter(prefix="/api/v1", tags=["bids"])


@router.get("/health")
def health() -> dict[str, str]:
    """Lightweight health check for the UI and deployment probes."""
    return {"status": "ok", "service": "velobid-api"}


@router.get("/projects", response_model=list[ConfigSummary])
def projects(
    archived: bool = Query(False, alias="archived"),
    auth: AuthContext = Depends(get_auth_context),
) -> list[ConfigSummary]:
    """List configured projects that can be priced from the UI."""
    return list_project_configs(show_archived=archived, bidder_id=auth.bidder_id)


@router.get("/projects/with-pricing", response_model=list[ProjectPricingResponse])
def projects_with_pricing(
    auth: AuthContext = Depends(get_auth_context),
) -> list[ProjectPricingResponse]:
    """List all projects with real pricing data computed via preview_bid()."""
    return list_projects_with_pricing(bidder_id=auth.bidder_id)


@router.get("/projects/export/csv")
def export_projects_csv(
    auth: AuthContext = Depends(get_auth_context),
) -> StreamingResponse:
    """Export the full project portfolio as a CSV download."""
    projects = list_projects_with_pricing(bidder_id=auth.bidder_id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Project ID",
        "Name",
        "City",
        "State",
        "Trade",
        "Status",
        "Archived",
        "Total Bid",
        "Total Material",
        "Total Labor",
        "Total Labor Hours",
        "Area (SF)",
        "Versions",
    ])
    for project in projects:
        writer.writerow([
            project.id,
            project.name,
            project.city or "",
            project.state or "",
            project.trade,
            project_status_label(project.status),
            "Yes" if project.archived else "No",
            project.total_bid,
            project.total_material,
            project.total_labor,
            project.total_labor_hours,
            project.area_sf or "",
            project.version_count,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="portfolio-summary.csv"'},
    )


@router.post("/projects", response_model=ProjectPricingResponse, status_code=201)
def create_project_route(
    request: CreateProjectRequest,
    auth: AuthContext = Depends(get_auth_context),
) -> ProjectPricingResponse:
    """Create a new project config."""
    try:
        return create_project(request, bidder_id=auth.bidder_id)
    except FileExistsError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.patch("/projects/{project_id}/archive")
def archive_project_route(
    project_id: str,
    auth: AuthContext = Depends(get_auth_context),
) -> dict:
    """Archive a project (set archived=True)."""
    try:
        return archive_project(project_id, archived=True, bidder_id=auth.bidder_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.patch("/projects/{project_id}/unarchive")
def unarchive_project_route(
    project_id: str,
    auth: AuthContext = Depends(get_auth_context),
) -> dict:
    """Unarchive a project (set archived=False)."""
    try:
        return archive_project(project_id, archived=False, bidder_id=auth.bidder_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/projects/bulk-archive")
def bulk_archive_project_route(
    request: BulkArchiveRequest,
    auth: AuthContext = Depends(get_auth_context),
) -> dict:
    """Archive or unarchive multiple projects at once."""
    return bulk_archive_project(
        ids=request.ids,
        archived=request.archived,
        bidder_id=auth.bidder_id,
    )


@router.get("/trades", response_model=list[ConfigSummary])
def trades() -> list[ConfigSummary]:
    """List configured trades that can be priced from the UI."""
    return list_trade_configs()


@router.post("/bids/preview", response_model=BidPreviewResponse)
def bid_preview(
    request: GenerateBidRequest,
    auth: AuthContext = Depends(get_auth_context),
) -> BidPreviewResponse:
    """Price a bid and return totals/line items without writing PDFs."""
    try:
        return preview_bid(request, bidder_id=auth.bidder_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/bids/generate", response_model=GenerateBidResponse)
def bid_generate(
    request: GenerateBidRequest,
    auth: AuthContext = Depends(get_auth_context),
) -> GenerateBidResponse:
    """Generate one or more bid PDFs and return downloadable file URLs."""
    try:
        return generate_bid_files(request, bidder_id=auth.bidder_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.websocket("/ws/bids/generate")
async def bid_generate_ws(websocket: WebSocket) -> None:
    """Generate bid PDFs over a websocket with simple progress events."""
    try:
        auth = parse_auth_context(websocket.headers.get("authorization"))
    except HTTPException:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    try:
        payload = await websocket.receive_json()
        request = GenerateBidRequest.model_validate(payload)

        await websocket.send_json({"event": "accepted", "message": "Request received"})
        await websocket.send_json({"event": "pricing", "message": "Building bid preview"})
        preview = preview_bid(request, bidder_id=auth.bidder_id)
        await websocket.send_json({"event": "preview", "data": preview.model_dump()})

        await websocket.send_json({"event": "generating", "message": "Rendering PDFs"})
        result = generate_bid_files(request, bidder_id=auth.bidder_id)
        await websocket.send_json({"event": "complete", "data": result.model_dump()})
    except WebSocketDisconnect:
        return
    except Exception as error:
        await websocket.send_json({"event": "error", "message": str(error)})
    finally:
        await websocket.close()


def _resolve_bid_pdf(project_id: str, trade: str, package: str, filename: str) -> Path:
    """Resolve a bid PDF path from the URL parameters, with path traversal protection."""
    safe_path = BID_PROJECTS_DIR / "api_generated" / project_id / trade / package / filename
    resolved = safe_path.resolve()
    # Ensure the resolved path stays inside BID_PROJECTS_DIR
    if not str(resolved).startswith(str(BID_PROJECTS_DIR.resolve())):
        raise HTTPException(status_code=403, detail="Invalid path")
    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return resolved


@router.get("/bids/{project_id}/{trade}/{package}/view/{filename}")
def view_bid_pdf(
    project_id: str,
    trade: str,
    package: str,
    filename: str,
    auth: AuthContext = Depends(get_auth_context),
) -> FileResponse:
    """View a generated bid PDF inline in the browser."""
    try:
        resolve_project_path(project_id, bidder_id=auth.bidder_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    resolved = _resolve_bid_pdf(project_id, trade, package, filename)
    return FileResponse(
        path=resolved,
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.get("/bids/{project_id}/{trade}/{package}/download/{filename}")
def download_bid_pdf(
    project_id: str,
    trade: str,
    package: str,
    filename: str,
    auth: AuthContext = Depends(get_auth_context),
) -> FileResponse:
    """Download a generated bid PDF as an attachment."""
    try:
        resolve_project_path(project_id, bidder_id=auth.bidder_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    resolved = _resolve_bid_pdf(project_id, trade, package, filename)
    return FileResponse(
        path=resolved,
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
