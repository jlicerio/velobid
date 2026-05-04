"""Bid API routes for UI integration."""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from api.schemas.bids import (
    BidPreviewResponse,
    ConfigSummary,
    GenerateBidRequest,
    GenerateBidResponse,
)
from api.services.bids import (
    generate_bid_files,
    list_project_configs,
    list_trade_configs,
    preview_bid,
)

router = APIRouter(prefix="/api/v1", tags=["bids"])


@router.get("/health")
def health() -> dict[str, str]:
    """Lightweight health check for the UI and deployment probes."""
    return {"status": "ok", "service": "velobid-api"}


@router.get("/projects", response_model=list[ConfigSummary])
def projects() -> list[ConfigSummary]:
    """List configured projects that can be priced from the UI."""
    return list_project_configs()


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
