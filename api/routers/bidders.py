"""API routes for bidder groups, users, and chat session management."""

from fastapi import APIRouter, HTTPException, Header, Request

from pydantic import BaseModel, Field

from api.schemas.bidders import (
    AddUserRequest,
    BidderGroupSummary,
    ChatRequestWithSession,
    CreateSessionRequest,
    SessionDetail,
    SessionInfo,
    UserInfoResponse,
)
from api.services.bidders import (
    add_user_to_bidder,
    create_session,
    get_bidder_group,
    get_bidder_name,
    get_session,
    get_session_messages,
    get_user,
    list_bidder_groups,
    list_user_sessions,
    list_users,
    append_session_messages,
    remove_user_from_bidder,
)

router = APIRouter(prefix="/api/v1", tags=["bidders"])


# ---------------------------------------------------------------------------
# Bidder Groups & Users
# ---------------------------------------------------------------------------


@router.get("/bidders", response_model=list[BidderGroupSummary])
def list_bidders():
    """List all bidder groups (contractor companies)."""
    return list_bidder_groups()


@router.get("/bidders/{bidder_id}/users", response_model=list[UserInfoResponse])
def list_bidder_users(bidder_id: str):
    """List all users in a bidder group."""
    return list_users(bidder_id)


# ---------------------------------------------------------------------------
# Chat Sessions
# ---------------------------------------------------------------------------


@router.post("/session", response_model=SessionInfo, status_code=201)
def create_chat_session(request: CreateSessionRequest):
    """Create a new chat session for a user in a bidder group."""
    # Validate bidder exists
    group = get_bidder_group(request.bidder_id)
    if not group:
        raise HTTPException(
            status_code=404,
            detail=f"Bidder group '{request.bidder_id}' not found",
        )

    # Validate user exists in bidder
    user = get_user(request.bidder_id, request.user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User '{request.user_id}' not found in bidder '{request.bidder_id}'",
        )

    return create_session(request.bidder_id, request.user_id, request.project_id)


@router.get("/session/{session_id}", response_model=SessionDetail)
def get_chat_session(session_id: str):
    """Get a chat session with full message history."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get(
    "/sessions/{bidder_id}/{user_id}", response_model=list[SessionInfo]
)
def list_chat_sessions(bidder_id: str, user_id: str):
    """List all chat sessions for a specific user."""
    return list_user_sessions(bidder_id, user_id)


class AppendMessagesRequest(BaseModel):
    """Request body for appending messages to a session."""

    messages: list[dict] = Field(..., examples=[[{"role": "user", "content": "Hello"}]])


@router.post("/session/{session_id}/messages", status_code=200)
def append_messages(session_id: str, body: AppendMessagesRequest):
    """Append messages to an existing chat session."""
    ok = append_session_messages(session_id, body.messages)
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": f"{len(body.messages)} message(s) appended", "session_id": session_id}


# ---------------------------------------------------------------------------
# User Management
# ---------------------------------------------------------------------------


class AddUserBody(BaseModel):
    """Request body for adding a user."""

    name: str = Field(..., examples=["Maria Hernandez"])
    role: str = Field("Estimator", examples=["Estimator", "Project Manager"])
    email: str | None = None
    password: str = Field(..., examples=["airhero2024"])


@router.post("/bidders/{bidder_id}/users", status_code=201)
def add_user(bidder_id: str, body: AddUserBody):
    """Add a user to a bidder group. Password is hashed automatically."""
    try:
        user = add_user_to_bidder(
            bidder_id=bidder_id,
            name=body.name,
            role=body.role,
            email=body.email,
            password=body.password,
        )
        return {"message": f"User '{body.name}' added", "user": user}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/bidders/{bidder_id}/users/{user_id}")
def delete_user(bidder_id: str, user_id: str):
    """Remove a user from a bidder group."""
    try:
        remove_user_from_bidder(bidder_id, user_id)
        return {"message": f"User '{user_id}' removed"}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
