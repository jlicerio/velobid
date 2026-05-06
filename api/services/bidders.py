"""Service layer for bidder groups, users, and chat session management."""

import hashlib
import json
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from jose import JWTError, jwt

from api.schemas.bidders import (
    BidderGroupSummary,
    ChatRequestWithSession,
    SessionDetail,
    SessionInfo,
    SessionMessage,
    UserInfo,
    UserInfoResponse,
)

from api.services.bids import PROJECT_ROOT

BIDDERS_DIR = PROJECT_ROOT / "config" / "bidders"
SESSIONS_DIR = PROJECT_ROOT / "bid_projects" / "sessions"

# ---------------------------------------------------------------------------
# Bidder & User helpers
# ---------------------------------------------------------------------------


def read_json(path: Path) -> dict:
    """Read a JSON file with BOM tolerance."""
    with path.open(encoding="utf-8-sig") as f:
        return json.load(f)


def write_json(path: Path, data) -> None:
    """Write JSON data to a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def list_bidder_groups() -> list[BidderGroupSummary]:
    """List all bidder groups with user counts."""
    results = []
    for dir_path in sorted(BIDDERS_DIR.iterdir()):
        if not dir_path.is_dir():
            continue
        bidder_file = dir_path / "bidder.json"
        if not bidder_file.exists():
            continue

        try:
            data = read_json(bidder_file)
            users = _load_users(dir_path)
            results.append(
                BidderGroupSummary(
                    id=dir_path.name,
                    company_name=data.get("company_name", dir_path.name),
                    user_count=len(users),
                )
            )
        except Exception:
            continue
    return results


def get_bidder_group(bidder_id: str) -> Optional[dict]:
    """Get bidder group data including users."""
    bidder_dir = BIDDERS_DIR / bidder_id
    bidder_file = bidder_dir / "bidder.json"
    if not bidder_file.exists():
        return None

    data = read_json(bidder_file)
    data["id"] = bidder_id
    data["users"] = [u.model_dump() for u in _load_users(bidder_dir)]
    return data


def list_users(bidder_id: str) -> list[UserInfoResponse]:
    """List users in a bidder group."""
    bidder_dir = BIDDERS_DIR / bidder_id
    if not (bidder_dir / "bidder.json").exists():
        return []

    users = _load_users(bidder_dir)
    return [
        UserInfoResponse(
            user_id=u.id,
            name=u.name,
            role=u.role,
            email=u.email,
        )
        for u in users
    ]


def _load_users(bidder_dir: Path) -> list[UserInfo]:
    """Load users from a bidder group's users.json (or bidder.json)."""
    users_file = bidder_dir / "users.json"
    if users_file.exists():
        try:
            raw = json.loads(users_file.read_text(encoding="utf-8-sig"))
            if isinstance(raw, list):
                return [UserInfo(**u) for u in raw]
        except Exception:
            pass

    # Fallback: check if bidder.json has an embedded "users" key
    bidder_file = bidder_dir / "bidder.json"
    if bidder_file.exists():
        try:
            data = read_json(bidder_file)
            embedded = data.get("users", [])
            if embedded:
                return [UserInfo(**u) for u in embedded]
        except Exception:
            pass

    # If no users configured, create a default user from bidder contact info
    try:
        data = read_json(bidder_file)
        contact_name = data.get("primary_contact", "Primary")
        return [
            UserInfo(
                id=bidder_dir.name,
                name=contact_name,
                role="Primary",
                email=data.get("contact_email"),
            )
        ]
    except Exception:
        return [UserInfo(id="default", name="Default User", role="User")]


def get_user(bidder_id: str, user_id: str) -> Optional[UserInfo]:
    """Get a specific user in a bidder group."""
    users = _load_users(BIDDERS_DIR / bidder_id)
    for u in users:
        if u.id == user_id:
            return u
    return None


def get_bidder_name(bidder_id: str) -> str:
    """Get the display name for a bidder group."""
    bidder_file = BIDDERS_DIR / bidder_id / "bidder.json"
    if bidder_file.exists():
        return read_json(bidder_file).get("company_name", bidder_id)
    return bidder_id


# ---------------------------------------------------------------------------
# Chat Session management
# ---------------------------------------------------------------------------


def create_session(bidder_id: str, user_id: str, project_id: Optional[str] = None) -> SessionInfo:
    """Create a new chat session for a user."""
    bidder_name = get_bidder_name(bidder_id)
    user = get_user(bidder_id, user_id)
    user_name = user.name if user else user_id

    session_id = _generate_session_id()
    now = _now_iso()

    session = {
        "session_id": session_id,
        "bidder_id": bidder_id,
        "bidder_name": bidder_name,
        "user_id": user_id,
        "user_name": user_name,
        "project_id": project_id,
        "created_at": now,
        "updated_at": now,
        "messages": [],
    }

    session_path = SESSIONS_DIR / f"{session_id}.json"
    write_json(session_path, session)

    return SessionInfo(
        session_id=session_id,
        bidder_id=bidder_id,
        bidder_name=bidder_name,
        user_id=user_id,
        user_name=user_name,
        message_count=0,
        created_at=now,
        updated_at=now,
    )


def get_session(session_id: str) -> Optional[SessionDetail]:
    """Get a full session with messages."""
    session_path = SESSIONS_DIR / f"{session_id}.json"
    if not session_path.exists():
        return None

    try:
        data = read_json(session_path)
        return SessionDetail(
            session_id=data["session_id"],
            bidder_id=data["bidder_id"],
            bidder_name=data.get("bidder_name", data["bidder_id"]),
            user_id=data["user_id"],
            user_name=data.get("user_name", data["user_id"]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            messages=[SessionMessage(**m) for m in data.get("messages", [])],
        )
    except Exception:
        return None


def get_session_messages(session_id: str) -> list[dict]:
    """Get raw message dicts from a session (for agent consumption)."""
    session_path = SESSIONS_DIR / f"{session_id}.json"
    if not session_path.exists():
        return []

    try:
        data = read_json(session_path)
        return data.get("messages", [])
    except Exception:
        return []


def append_session_messages(session_id: str, messages: list[dict]) -> bool:
    """Append messages to a session's history."""
    session_path = SESSIONS_DIR / f"{session_id}.json"
    if not session_path.exists():
        return False

    try:
        data = read_json(session_path)
        now = _now_iso()

        for msg in messages:
            msg["timestamp"] = now
            data["messages"].append(msg)

        data["updated_at"] = now
        write_json(session_path, data)
        return True
    except Exception:
        return False


def list_user_sessions(bidder_id: str, user_id: str) -> list[SessionInfo]:
    """List all sessions for a specific user."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    for path in SESSIONS_DIR.glob("*.json"):
        try:
            data = read_json(path)
            if data.get("bidder_id") == bidder_id and data.get("user_id") == user_id:
                results.append(
                    SessionInfo(
                        session_id=data["session_id"],
                        bidder_id=data["bidder_id"],
                        bidder_name=data.get("bidder_name", data["bidder_id"]),
                        user_id=data["user_id"],
                        user_name=data.get("user_name", data["user_id"]),
                        message_count=len(data.get("messages", [])),
                        created_at=data["created_at"],
                        updated_at=data["updated_at"],
                    )
                )
        except Exception:
            continue
    # Sort by most recent first
    results.sort(key=lambda s: s.updated_at, reverse=True)
    return results


def _generate_session_id() -> str:
    """Generate a short unique session ID."""
    return uuid.uuid4().hex[:12]


def _now_iso() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def _get_jwt_secret() -> str:
    """Return JWT signing secret.

    Production deployments must set JWT_SECRET. Local/dev can use a visible
    fallback so Docker smoke tests continue to work, but it is never silent.
    """
    secret = os.getenv("JWT_SECRET")
    if secret:
        return secret

    env = os.getenv("VELO_ENV", os.getenv("APP_ENV", "development")).lower()
    if env in {"prod", "production"}:
        raise RuntimeError("JWT_SECRET must be set in production")

    logging.getLogger(__name__).warning(
        "JWT_SECRET is not set; using insecure development-only JWT secret."
    )
    return "velobid-development-only-jwt-secret"


_JWT_SECRET = _get_jwt_secret()
_JWT_ALGORITHM = "HS256"
_JWT_EXPIRE_HOURS = 24


def verify_password(plain: str, salt: str, stored_hash: str) -> bool:
    """Verify a password against its salted SHA256 hash."""
    computed = hashlib.sha256((salt + plain).encode()).hexdigest()
    return computed == stored_hash


def authenticate_user(bidder_id: str, user_id: str, password: str) -> Optional[dict]:
    """Authenticate a user. Returns user dict on success, None on failure."""
    users = _load_users(BIDDERS_DIR / bidder_id)
    for user in users:
        if user.id == user_id:
            # Check if user has password fields
            user_dict = _get_raw_user(BIDDERS_DIR / bidder_id, user_id)
            if user_dict and "password_hash" in user_dict and "password_salt" in user_dict:
                if verify_password(password, user_dict["password_salt"], user_dict["password_hash"]):
                    return user_dict
            return None
    return None


def _get_raw_user(bidder_dir: Path, user_id: str) -> Optional[dict]:
    """Get raw user dict from users.json or bidder.json."""
    users_file = bidder_dir / "users.json"
    if users_file.exists():
        try:
            data = json.loads(users_file.read_text(encoding="utf-8-sig"))
            if isinstance(data, list):
                for u in data:
                    if u.get("id") == user_id:
                        return u
        except Exception:
            pass
    return None


def create_token(bidder_id: str, user_id: str) -> str:
    """Create a JWT token for a user."""
    expire = datetime.now(timezone.utc) + timedelta(hours=_JWT_EXPIRE_HOURS)
    payload = {
        "bidder_id": bidder_id,
        "user_id": user_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, _JWT_SECRET, algorithm=_JWT_ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    """Verify a JWT token. Returns payload dict on success, None on failure."""
    try:
        payload = jwt.decode(token, _JWT_SECRET, algorithms=[_JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


# ---------------------------------------------------------------------------
# User CRUD
# ---------------------------------------------------------------------------


def _user_id_from_name(name: str) -> str:
    """Convert a user name to a snake_case user ID."""
    import re
    return re.sub(r"[^a-z0-9_]", "", name.lower().replace(" ", "_"))


def add_user_to_bidder(
    bidder_id: str, name: str, role: str = "Estimator",
    email: str | None = None, password: str | None = None,
) -> dict:
    """Add a user to a bidder group. Writes to users.json immediately."""
    bidder_dir = BIDDERS_DIR / bidder_id
    users_file = bidder_dir / "users.json"

    if not (bidder_dir / "bidder.json").exists():
        raise FileNotFoundError(f"Bidder group '{bidder_id}' not found")

    user_id = _user_id_from_name(name)

    # Load existing users
    users = []
    if users_file.exists():
        try:
            users = json.loads(users_file.read_text(encoding="utf-8-sig"))
            if not isinstance(users, list):
                users = []
        except Exception:
            users = []

    # Check for duplicate
    for u in users:
        if u.get("id") == user_id:
            raise ValueError(f"User '{user_id}' already exists")

    # Build user entry
    user_entry = {"id": user_id, "name": name, "role": role}
    if email:
        user_entry["email"] = email
    if password:
        import secrets
        salt = secrets.token_hex(16)
        user_entry["password_salt"] = salt
        user_entry["password_hash"] = hashlib.sha256((salt + password).encode()).hexdigest()

    users.append(user_entry)
    users_file.write_text(json.dumps(users, indent=2), encoding="utf-8")
    return user_entry


def remove_user_from_bidder(bidder_id: str, user_id: str) -> None:
    """Remove a user from a bidder group."""
    bidder_dir = BIDDERS_DIR / bidder_id
    users_file = bidder_dir / "users.json"

    if not users_file.exists():
        raise FileNotFoundError(f"No users file for bidder '{bidder_id}'")

    try:
        users = json.loads(users_file.read_text(encoding="utf-8-sig"))
        if not isinstance(users, list):
            raise ValueError("Invalid users file format")
    except Exception:
        raise ValueError("Invalid users file format")

    before = len(users)
    users = [u for u in users if u.get("id") != user_id]

    if len(users) == before:
        raise FileNotFoundError(f"User '{user_id}' not found")

    users_file.write_text(json.dumps(users, indent=2), encoding="utf-8")
