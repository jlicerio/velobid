"""FastAPI router for proxying chat to the Hermes agent container."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.routers.agent_chat import ChatMessage
from api.services.agent_access import AgentAccessError, enforce_agent_access
from api.services.auth_guard import AuthContext, get_auth_context
from api.services.hermes_proxy import proxy_chat_to_hermes

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


class HermesChatRequest(BaseModel):
    messages: List[ChatMessage]
    project_id: Optional[str] = None
    trade: Optional[str] = "hvac"
    bidder_id: Optional[str] = None


@router.post("/hermes-chat")
async def hermes_chat_endpoint(
    request: HermesChatRequest,
    auth: AuthContext = Depends(get_auth_context),
):
    """Proxy chat through the containerized Hermes agent (no tool loop / context injection)."""
    try:
        enforce_agent_access(auth.bidder_id, auth.user_id)
    except AgentAccessError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail,
            headers=error.headers,
        ) from None

    messages = [m.model_dump() for m in request.messages]
    return StreamingResponse(
        proxy_chat_to_hermes(messages, bidder_id=auth.bidder_id, project_id=request.project_id),
        media_type="text/event-stream",
    )
