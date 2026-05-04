import asyncio
import json
from typing import Any, Dict, List, Optional

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel


class StateUpdate(BaseModel):
    project_id: Optional[str] = None
    trade: Optional[str] = None
    region: Optional[str] = None
    line_items: Optional[List[Dict[str, Any]]] = None
    pricing: Optional[Dict[str, Any]] = None


class BidStateManager:
    """Manages active bid sessions with real-time sync."""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.session_states: Dict[str, Dict[str, Any]] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)

        # Send initial state if it exists
        if session_id in self.session_states:
            await websocket.send_json(
                {"type": "state_init", "data": self.session_states[session_id]}
            )

    def disconnect(self, session_id: str, websocket: WebSocket):
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)

    async def broadcast_change(
        self, session_id: str, update: Dict[str, Any], sender: Optional[WebSocket] = None
    ):
        """Broadcast an edit to all connected clients in a session."""
        if session_id not in self.session_states:
            self.session_states[session_id] = {}

        # Merge update into state
        self.session_states[session_id].update(update)

        message = {
            "type": "state_update",
            "data": update,
            "full_state": self.session_states[session_id],
        }

        for connection in self.active_connections.get(session_id, []):
            if connection != sender:
                await connection.send_json(message)


state_manager = BidStateManager()
