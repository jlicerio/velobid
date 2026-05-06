"""FastAPI router for proxying chat to the Hermes agent container."""

from typing import List, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.routers.agent_chat import ChatMessage
from api.services.hermes_proxy import proxy_chat_to_hermes

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


class HermesChatRequest(BaseModel):
    messages: List[ChatMessage]
    project_id: Optional[str] = None
    trade: Optional[str] = "hvac"
    bidder_id: Optional[str] = None


@router.post("/hermes-chat")
async def hermes_chat_endpoint(request: HermesChatRequest):
    """Proxy chat through the containerized Hermes agent (no tool loop / context injection)."""
    messages = [m.model_dump() for m in request.messages]
    return StreamingResponse(
        proxy_chat_to_hermes(messages, bidder_id=request.bidder_id, project_id=request.project_id),
        media_type="text/event-stream",
    )
