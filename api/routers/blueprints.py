"""Blueprint API routes for uploading, listing, and retrieving blueprints."""

from fastapi import APIRouter, HTTPException, UploadFile

from api.schemas.blueprints import (
    BlueprintDetailResponse,
    BlueprintListResponse,
    BlueprintUploadResponse,
)
from api.services.blueprints import (
    get_blueprint,
    list_blueprints,
    save_blueprint,
)

router = APIRouter(prefix="/api/v1", tags=["blueprints"])


@router.post(
    "/blueprints/{project_id}",
    response_model=BlueprintUploadResponse,
    summary="Upload a blueprint file",
    description="Upload a blueprint PDF or image for a given project. "
    "PDF files are automatically split into individual PNG page images. "
    "Accepted formats: PDF, PNG, JPG, JPEG, TIFF. Max file size: 50 MB.",
)
async def upload_blueprint(project_id: str, file: UploadFile) -> BlueprintUploadResponse:
    """Upload a blueprint file (multipart form, field name ``file``).

    The uploaded file is saved to::

        bid_projects/api_generated/{project_id}/blueprints/{blueprint_id}/

    A JSON metadata sidecar is written alongside the file. For PDF uploads,
    ``pdf2image`` is used to extract each page as a separate PNG stored in a
    ``pages/`` subdirectory.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided in upload.")

    try:
        result = save_blueprint(
            project_id=project_id,
            filename=file.filename,
            file_obj=file.file,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/blueprints/{project_id}",
    response_model=BlueprintListResponse,
    summary="List blueprints for a project",
    description="Return a summary list of all blueprints uploaded for the given project.",
)
def list_project_blueprints(project_id: str) -> BlueprintListResponse:
    """List all blueprints stored under a project."""
    try:
        return list_blueprints(project_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get(
    "/blueprints/{project_id}/{blueprint_id}",
    response_model=BlueprintDetailResponse,
    summary="Get blueprint details",
    description="Return full details for a single blueprint including extracted page images.",
)
def get_blueprint_detail(project_id: str, blueprint_id: str) -> BlueprintDetailResponse:
    """Retrieve metadata and page info for a specific blueprint."""
    try:
        return get_blueprint(project_id, blueprint_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
