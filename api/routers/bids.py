"""Bid API routes for UI integration."""

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect

from api.schemas.bids import (
    BidPreviewResponse,
    ConfigSummary,
    CreateProjectRequest,
    GenerateBidRequest,
    GenerateBidResponse,
    ProjectPricingResponse,
)
from api.services.bids import (
    archive_project,
    create_project,
    generate_bid_files,
    list_project_configs,
    list_projects_with_pricing,
    list_trade_configs,
    preview_bid,
)

router = APIRouter(prefix="/api/v1", tags=["bids"])


@router.get("/health")
def health() -> dict[str, str]:
    """Lightweight health check for the UI and deployment probes."""
    return {"status": "ok", "service": "velobid-api"}


@router.get("/projects", response_model=list[ConfigSummary])
def projects(archived: bool = Query(False, alias="archived")) -> list[ConfigSummary]:
    """List configured projects that can be priced from the UI."""
    return list_project_configs(show_archived=archived)


@router.get("/projects/with-pricing", response_model=list[ProjectPricingResponse])
def projects_with_pricing() -> list[ProjectPricingResponse]:
    """List all projects with real pricing data computed via preview_bid()."""
    return list_projects_with_pricing()


@router.post("/projects", response_model=ProjectPricingResponse, status_code=201)
def create_project_route(request: CreateProjectRequest) -> ProjectPricingResponse:
    """Create a new project config."""
    try:
        return create_project(request)
    except FileExistsError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.patch("/projects/{project_id}/archive")
def archive_project_route(project_id: str) -> dict:
    """Archive a project (set archived=True)."""
    try:
        return archive_project(project_id, archived=True)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.patch("/projects/{project_id}/unarchive")
def unarchive_project_route(project_id: str) -> dict:
    """Unarchive a project (set archived=False)."""
    try:
        return archive_project(project_id, archived=False)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/trades", response_model=list[ConfigSummary])
def trades() -> list[ConfigSummary]:
    """List configured trades that can be priced from the UI."""
    return list_trade_configs()


@router.post("/bids/preview", response_model=BidPreviewResponse)
def bid_preview(request: GenerateBidRequest) -> BidPreviewResponse:
    """Price a bid and return totals/line items without writing PDFs."""
    try:
        return preview_bid(request)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/bids/generate", response_model=GenerateBidResponse)
def bid_generate(request: GenerateBidRequest) -> GenerateBidResponse:
    """Generate one or more bid PDFs and return downloadable file URLs."""
    try:
        return generate_bid_files(request)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.websocket("/ws/bids/generate")
async def bid_generate_ws(websocket: WebSocket) -> None:
    """Generate bid PDFs over a websocket with simple progress events."""
    await websocket.accept()
    try:
        payload = await websocket.receive_json()
        request = GenerateBidRequest.model_validate(payload)

        await websocket.send_json({"event": "accepted", "message": "Request received"})
        await websocket.send_json({"event": "pricing", "message": "Building bid preview"})
        preview = preview_bid(request)
        await websocket.send_json({"event": "preview", "data": preview.model_dump()})

        await websocket.send_json({"event": "generating", "message": "Rendering PDFs"})
        result = generate_bid_files(request)
        await websocket.send_json({"event": "complete", "data": result.model_dump()})
    except WebSocketDisconnect:
        return
    except Exception as error:
        await websocket.send_json({"event": "error", "message": str(error)})
    finally:
        await websocket.close()
