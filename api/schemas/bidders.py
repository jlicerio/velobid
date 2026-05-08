"""Pydantic schemas for bidder groups, users, and chat sessions."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class UserInfo(BaseModel):
    """A user belonging to a bidder group."""

    id: str = Field(..., examples=["jose"])
    name: str = Field(..., examples=["Jose Exiga"])
    role: str = Field("Estimator", examples=["Estimator", "Project Manager"])
    email: Optional[str] = None


class BidderGroup(BaseModel):
    """A bidder company/group that contains users."""

    id: str = Field(..., examples=["air_hero"])
    company_name: str
    primary_contact: Optional[str] = None
    users: list[UserInfo] = []


class UserInfoResponse(BaseModel):
    """User info returned from API."""

    user_id: str
    name: str
    role: str
    email: Optional[str] = None


class BidderGroupSummary(BaseModel):
    """Bidder group summary for listing."""

    id: str
    company_name: str
    user_count: int = 0


class CreateSessionRequest(BaseModel):
    """Create a new chat session for a user."""

    bidder_id: str = Field(..., examples=["air_hero"])
    user_id: str = Field(..., examples=["jose"])
    project_id: Optional[str] = Field(None, examples=["jackson_mcallen_42740"])


class SessionInfo(BaseModel):
    """Chat session info returned to the client."""

    session_id: str
    bidder_id: str
    bidder_name: str
    user_id: str
    user_name: str
    message_count: int = 0
    created_at: str
    updated_at: str


class SessionMessage(BaseModel):
    """A single message in a session."""

    role: str
    content: Optional[str] = None
    reasoning_content: Optional[str] = None
    tool_calls: Optional[list[dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None
    timestamp: Optional[str] = None


class SessionDetail(BaseModel):
    """Full session with message history."""

    session_id: str
    bidder_id: str
    bidder_name: str
    user_id: str
    user_name: str
    created_at: str
    updated_at: str
    messages: list[SessionMessage] = []


class ChatRequestWithSession(BaseModel):
    """Chat request that includes session context."""

    session_id: str
    message: str
    project_id: Optional[str] = None
    trade: str = "hvac"


# ---------------------------------------------------------------------------
# Auth schemas
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    """User login credentials."""

    bidder_id: str | None = Field(
        default=None,
        examples=["air_hero"],
        description="Optional company identifier. If omitted, login resolves by user_id + password.",
    )
    user_id: str = Field(..., examples=["jose"])
    password: str = Field(..., examples=["airhero2024"])


class LoginResponse(BaseModel):
    """Login response with JWT token."""

    token: str
    token_type: str = "bearer"
    user: UserInfoResponse
    bidder_id: str
    bidder_name: str


class TokenData(BaseModel):
    """Data encoded in the JWT."""

    bidder_id: str
    user_id: str
    exp: Optional[int] = None


class AddUserRequest(BaseModel):
    """Request to add a new user."""

    name: str
    role: str = "Estimator"
    email: Optional[str] = None
    password: str
