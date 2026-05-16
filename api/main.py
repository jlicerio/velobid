"""FastAPI application entrypoint for the Velobid UI/API."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from api.routers.admin_bidders import router as admin_bidders_router
from api.routers.agent_chat import router as agent_router
from api.routers.ai import router as ai_router
from api.routers.auth import router as auth_router
from api.routers.bidders import router as bidders_router
from api.routers.bids import router as bids_router
from api.routers.billing import router as billing_router
from api.routers.blueprints import router as blueprints_router
from api.routers.files import router as files_router
from api.routers.hermes_chat import router as hermes_chat_router
from api.routers.integrations import router as integrations_router
from api.routers.residential import router as residential_router
from api.routers.settings import router as settings_router
from api.routers.sync import router as sync_router
from api.routers.versions import router as versions_router
from api.routers.vision import router as vision_router
from api.services.bids import BID_PROJECTS_DIR, PROJECT_ROOT

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="Velobid API",
    description="Modular REST and websocket layer for bid previews and PDF generation.",
    version="0.1.1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bids_router)
app.include_router(billing_router)
app.include_router(ai_router)
app.include_router(files_router)
app.include_router(sync_router)
app.include_router(agent_router)
app.include_router(hermes_chat_router)
app.include_router(versions_router)
app.include_router(vision_router)
app.include_router(blueprints_router)
app.include_router(bidders_router)
app.include_router(auth_router)
app.include_router(residential_router)
app.include_router(admin_bidders_router)
app.include_router(integrations_router)
app.include_router(settings_router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")
app.mount("/files", StaticFiles(directory=BID_PROJECTS_DIR), name="files")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    """Serve the lightweight built-in UI."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/v1/meta")
def meta() -> dict[str, str]:
    """Expose basic runtime paths for debugging local setup."""
    return {
        "project_root": str(PROJECT_ROOT),
        "bid_projects_dir": str(BID_PROJECTS_DIR),
    }


@app.get("/{path:path}", include_in_schema=False)
async def spa_fallback(path: str):
    """Serve SPA index.html for client-side routes (e.g. /login, /logout)."""
    return FileResponse(STATIC_DIR / "index.html")
