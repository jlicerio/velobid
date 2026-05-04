import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.services.state import state_manager

router = APIRouter(prefix="/ws/sync", tags=["sync"])


@router.websocket("/{session_id}")
async def sync_bid_state(websocket: WebSocket, session_id: str):
    """Real-time bid state synchronization (Bolt-style)."""
    await state_manager.connect(session_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # data expected to be a partial update or an action
            if data.get("type") == "edit":
                update = data.get("update", {})
                await state_manager.broadcast_change(session_id, update, sender=websocket)
            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        state_manager.disconnect(session_id, websocket)
