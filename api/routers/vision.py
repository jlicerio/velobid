"""FastAPI router for blueprint vision analysis endpoints."""

import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.services.bids import BID_PROJECTS_DIR
from api.services.vision import analyze_blueprint_page

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/vision", tags=["vision"])

BLUEPRINTS_DIR_NAME = "blueprints"
PAGES_DIR_NAME = "pages"


class AnalysisResponse(BaseModel):
    """Response model for blueprint analysis results."""

    project_id: str
    blueprint_id: str
    page_num: int
    equipment: list[dict]
    ductwork: list[dict]
    piping: list[dict]
    fixtures: list[dict]
    rooms: list[dict]
    notes: list[dict]
    sidecar_path: str


def _resolve_blueprint_page_path(
    project_id: str,
    blueprint_id: str,
    page_num: int,
) -> Path:
    """Resolve the file system path for a blueprint page image.

    Convention:
      {BID_PROJECTS_DIR}/api_generated/{project_id}/blueprints/{blueprint_id}/pages/page_{page_num:02d}.png

    Args:
        project_id: The project identifier (e.g., "shalom_prayer_center")
        blueprint_id: The blueprint set identifier (e.g., "MEP_Floor_1")
        page_num: The 1-indexed page number

    Returns:
        Path to the page image file

    Raises:
        HTTPException: If the path doesn't exist or is invalid
    """
    # Build expected paths
    project_dir = (BID_PROJECTS_DIR / "api_generated" / project_id).resolve()
    blueprint_dir = project_dir / BLUEPRINTS_DIR_NAME / blueprint_id
    pages_dir = blueprint_dir / PAGES_DIR_NAME

    # Check common image formats
    image_paths = []
    for ext in [".png", ".jpg", ".jpeg", ".webp", ".gif"]:
        candidate = pages_dir / f"page_{page_num:02d}{ext}"
        if candidate.exists():
            image_paths.append(candidate)
            break

    # Try without zero-padding
    if not image_paths:
        for ext in [".png", ".jpg", ".jpeg", ".webp", ".gif"]:
            candidate = pages_dir / f"page_{page_num}{ext}"
            if candidate.exists():
                image_paths.append(candidate)
                break

    if not image_paths:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Blueprint page not found. "
                f"Searched in {pages_dir} for page_{page_num:02d}.* and page_{page_num}.*"
            ),
        )

    # Validate we don't traverse outside allowed directory
    resolved = image_paths[0].resolve()
    allowed = (BID_PROJECTS_DIR / "api_generated").resolve()
    if not str(resolved).startswith(str(allowed)):
        raise HTTPException(
            status_code=403,
            detail="Access denied: path traversal detected",
        )

    return resolved


@router.post("/analyze/{project_id}/{blueprint_id}", response_model=AnalysisResponse)
@router.post("/analyze/{project_id}/{blueprint_id}/{page_num}", response_model=AnalysisResponse)
def analyze_blueprint(
    project_id: str,
    blueprint_id: str,
    page_num: int = 1,
) -> AnalysisResponse:
    """Analyze a blueprint page image using xAI Grok Vision.

    Extracts MEP (Mechanical, Electrical, Plumbing) quantities and details
    from the specified blueprint page.

    Args:
        project_id: Project identifier (e.g., "shalom_prayer_center")
        blueprint_id: Blueprint set identifier (e.g., "MEP_Floor_1")
        page_num: Page number to analyze (1-indexed, default: 1)

    Returns:
        Structured takeoff data parsed from the vision API response
    """
    logger.info(
        "Analyzing blueprint: project=%s, blueprint=%s, page=%d",
        project_id,
        blueprint_id,
        page_num,
    )

    # Resolve the page image path
    image_path = _resolve_blueprint_page_path(project_id, blueprint_id, page_num)

    # Call the vision service
    try:
        result = analyze_blueprint_page(str(image_path))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ConnectionError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Vision API unavailable: {exc}",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Vision API returned invalid data: {exc}",
        )

    # Build sidecar path for response
    blueprint_dir = image_path.parent.parent
    sidecar_name = f"analysis_{page_num}.json"
    sidecar_path = blueprint_dir / sidecar_name

    return AnalysisResponse(
        project_id=project_id,
        blueprint_id=blueprint_id,
        page_num=page_num,
        equipment=result.get("equipment", []),
        ductwork=result.get("ductwork", []),
        piping=result.get("piping", []),
        fixtures=result.get("fixtures", []),
        rooms=result.get("rooms", []),
        notes=result.get("notes", []),
        sidecar_path=str(sidecar_path),
    )
