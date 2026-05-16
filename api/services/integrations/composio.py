"""
Composio integration service — multi-tenant, one-click OAuth for Gmail, Google Drive, etc.

Architecture:
  - One Composio API key for the whole VeloBid platform.
  - Each bidder is mapped to a Composio ``user_id`` (the bidder's slug).
  - Tools are fetched *per bidder* so connections are fully isolated.
  - OAuth callback URLs include ?bidder_id=... so we know who just connected.

Dependency: ``pip install composio-core``.  If the package is missing the module
degrades gracefully (no tools injected, OAuth endpoints return 501).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── lazy import ──────────────────────────────────────────────────────────────

_COMPOSIO_AVAILABLE: bool | None = None


def _composio_available() -> bool:
    """Return True when ``composio`` can be imported."""
    global _COMPOSIO_AVAILABLE
    if _COMPOSIO_AVAILABLE is None:
        try:
            import composio  # noqa: F401

            _COMPOSIO_AVAILABLE = True
        except ImportError:
            logger.warning("composio-core is not installed — integrations disabled")
            _COMPOSIO_AVAILABLE = False
    return _COMPOSIO_AVAILABLE


# ── config ───────────────────────────────────────────────────────────────────

# Which toolkits VeloBid exposes to bidders.
# Add more as needed (SLACK, GITHUB, NOTION, …).
_DEFAULT_TOOLKITS = ["GMAIL", "GOOGLE_DRIVE"]


# ── helpers ──────────────────────────────────────────────────────────────────


def _bidder_user_id(bidder_id: str) -> str:
    """Map a VeloBid bidder slug to a Composio user_id."""
    return f"velobid-{bidder_id}"


# ── public API ───────────────────────────────────────────────────────────────


def get_composio_client():
    """Return a configured Composio client (singleton-ish).

    Requires ``COMPOSIO_API_KEY`` in the environment.
    """
    if not _composio_available():
        return None

    import os

    from composio import Composio  # type: ignore[import-untyped]

    api_key = os.getenv("COMPOSIO_API_KEY", "")
    if not api_key:
        logger.warning("COMPOSIO_API_KEY is not set — integrations disabled")
        return None

    return Composio(api_key=api_key)


def get_connection_status(bidder_id: str) -> Dict[str, str]:
    """Return {toolkit_name: status} for every default toolkit.

    Statuses: ``"not_connected"`` | ``"connected"`` | ``"unknown"``
    """
    if not _composio_available():
        return {t: "not_available" for t in _DEFAULT_TOOLKITS}

    client = get_composio_client()
    if client is None:
        return {t: "not_configured" for t in _DEFAULT_TOOLKITS}

    user_id = _bidder_user_id(bidder_id)
    statuses: Dict[str, str] = {}

    try:
        # Get all connections for this user
        connections = client.connections.list(user_id=user_id)
        connected_apps = {
            c.get("appName", "").upper()
            for c in connections
            if c.get("status") == "active"
        }
    except Exception:
        logger.debug("Failed to list connections for %s", user_id, exc_info=True)
        connected_apps = set()

    for toolkit in _DEFAULT_TOOLKITS:
        statuses[toolkit] = (
            "connected" if toolkit.upper() in connected_apps else "not_connected"
        )

    return statuses


def get_tools_for_bidder(
    bidder_id: str, toolkits: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Return OpenAI-compatible tool definitions for a bidder's connected apps.

    Only returns tools for toolkits the bidder has actually connected.
    If the bidder has no active connections the list is empty.

    Parameters
    ----------
    bidder_id : str
        VeloBid bidder slug (e.g. ``"test_corp"``).
    toolkits : list[str] | None
        Toolkits to fetch.  Defaults to ``_DEFAULT_TOOLKITS``.

    Returns
    -------
    list[dict]
        Tool definitions in OpenAI function-calling format.
    """
    if not _composio_available():
        return []

    client = get_composio_client()
    if client is None:
        return []

    toolkits = toolkits or _DEFAULT_TOOLKITS
    user_id = _bidder_user_id(bidder_id)

    try:
        composio_tools = client.tools.get(user_id=user_id, toolkits=toolkits)
    except Exception:
        logger.exception("Failed to fetch tools for bidder %s", bidder_id)
        return []

    # Convert Composio tool objects → OpenAI function-calling dicts
    result: List[Dict[str, Any]] = []
    for tool in composio_tools:
        try:
            result.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.parameters or {},
                    },
                }
            )
        except Exception:
            logger.debug(
                "Skipping tool %s — serialization error",
                getattr(tool, "name", "?"),
                exc_info=True,
            )

    return result


def execute_tool_for_bidder(
    bidder_id: str, tool_name: str, arguments: Dict[str, Any]
) -> str:
    """Execute a Composio tool on behalf of a bidder and return the result string.

    Parameters
    ----------
    bidder_id : str
        VeloBid bidder slug.
    tool_name : str
        Composio tool name (e.g. ``"GMAIL_SEND_EMAIL"``).
    arguments : dict
        Tool arguments as a JSON-serialisable dict.

    Returns
    -------
    str
        Tool output as text (or an error message).
    """
    if not _composio_available():
        return "Composio is not installed — tool execution is unavailable."

    client = get_composio_client()
    if client is None:
        return "Composio API key is not configured — tool execution is unavailable."

    user_id = _bidder_user_id(bidder_id)

    try:
        result = client.tools.execute(
            user_id=user_id,
            tool_name=tool_name,
            arguments=arguments,
        )
        return str(result)
    except Exception:
        logger.exception(
            "Tool execution failed: %s for bidder %s", tool_name, bidder_id
        )
        return f"Tool execution failed: {tool_name}"


def initiate_oauth(bidder_id: str, toolkit: str, redirect_base: str) -> Optional[str]:
    """Start an OAuth flow for a toolkit and return the URL the user should visit.

    Parameters
    ----------
    bidder_id : str
        VeloBid bidder slug.
    toolkit : str
        Composio app name (e.g. ``"GMAIL"``, ``"GOOGLE_DRIVE"``).
    redirect_base : str
        Base URL of the VeloBid API (used to build the callback).

    Returns
    -------
    str | None
        OAuth URL to redirect the user to, or ``None`` on failure.
    """
    if not _composio_available():
        return None

    client = get_composio_client()
    if client is None:
        return None

    user_id = _bidder_user_id(bidder_id)
    redirect_url = f"{redirect_base.rstrip('/')}/api/v1/integrations/oauth/callback?bidder_id={bidder_id}"

    try:
        connection = client.connections.initiate(
            user_id=user_id,
            app=toolkit.upper(),
            redirect_url=redirect_url,
        )
        return connection.get("redirectUrl") or connection.get("redirect_url")
    except Exception:
        logger.exception("Failed to initiate OAuth for %s / %s", bidder_id, toolkit)
        return None


def disconnect(bidder_id: str, toolkit: str) -> bool:
    """Revoke a bidder's connection to a toolkit.

    Returns True on success.
    """
    if not _composio_available():
        return False

    client = get_composio_client()
    if client is None:
        return False

    user_id = _bidder_user_id(bidder_id)

    try:
        client.connections.delete(user_id=user_id, app=toolkit.upper())
        return True
    except Exception:
        logger.exception("Failed to disconnect %s from %s", bidder_id, toolkit)
        return False
