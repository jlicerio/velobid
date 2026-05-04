"""FastAPI application entrypoint for the Velobid UI/API."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routers.agent_chat import router as agent_router
from api.routers.ai import router as ai_router
from api.routers.bids import router as bids_router
from api.routers.files import router as files_router
from api.routers.sync import router as sync_router
from api.routers.versions import router as versions_router
from api.routers.blueprints import router as blueprints_router
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
app.include_router(ai_router)
app.include_router(files_router)
app.include_router(sync_router)
app.include_router(agent_router)
app.include_router(versions_router)
app.include_router(vision_router)
app.include_router(blueprints_router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
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

