import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.services.bids import BID_PROJECTS_DIR

router = APIRouter(prefix="/api/v1/files", tags=["files"])


class FileOperationRequest(BaseModel):
    path: str
    new_path: Optional[str] = None


@router.get("/list")
def list_files(subpath: str = ""):
    """List files in the generated output directory."""
    root = BID_PROJECTS_DIR / subpath
    if not root.exists() or not root.is_dir():
        raise HTTPException(status_code=404, detail="Path not found")

    items = []
    for item in root.iterdir():
        items.append(
            {
                "name": item.name,
                "is_dir": item.is_dir(),
                "path": str(item.relative_to(BID_PROJECTS_DIR)).replace("\\", "/"),
                "size": item.stat().st_size if item.is_file() else None,
            }
        )
    return items


@router.delete("/delete")
def delete_file(path: str):
    """Delete a generated file."""
    full_path = (BID_PROJECTS_DIR / path).resolve()
    if not str(full_path).startswith(str(BID_PROJECTS_DIR)):
        raise HTTPException(status_code=403, detail="Forbidden")

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if full_path.is_file():
        full_path.unlink()
    else:
        # For safety, don't allow recursive dir delete here yet
        raise HTTPException(status_code=400, detail="Cannot delete directory")

    return {"message": "Deleted successfully"}
