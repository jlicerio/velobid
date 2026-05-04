"""Pydantic schemas for blueprint upload and retrieval."""

from datetime import datetime

from pydantic import BaseModel, Field


class BlueprintPage(BaseModel):
    """Describes a single page image extracted from a blueprint upload."""

    page_number: int = Field(..., description="1-based page index")
    filename: str = Field(..., description="Page image filename")
    path: str = Field(..., description="Relative path from storage root")
    url: str = Field(..., description="Download URL for the page image")
    width: int | None = Field(None, description="Image width in pixels")
    height: int | None = Field(None, description="Image height in pixels")


class BlueprintUploadResponse(BaseModel):
    """Returned after a successful blueprint upload."""

    blueprint_id: str = Field(..., description="Unique identifier for this blueprint")
    project_id: str = Field(..., description="Project this blueprint belongs to")
    original_filename: str = Field(..., description="Name of the uploaded file")
    file_extension: str = Field(..., description="Extension of the original file")
    file_size_bytes: int = Field(..., description="Size of the uploaded file in bytes")
    page_count: int = Field(..., description="Number of pages (1 for images)")
    page_images: list[BlueprintPage] = Field(
        default_factory=list, description="List of extracted page images"
    )
    is_pdf: bool = Field(..., description="Whether the upload was a multi-page PDF")
    uploaded_at: str = Field(..., description="ISO-8601 upload timestamp")
    metadata_path: str = Field(..., description="Relative path to the JSON sidecar file")


class BlueprintListItem(BaseModel):
    """Summary of a stored blueprint for listing endpoints."""

    blueprint_id: str
    project_id: str
    original_filename: str
    file_extension: str
    file_size_bytes: int
    page_count: int
    is_pdf: bool
    uploaded_at: str


class BlueprintListResponse(BaseModel):
    """Response wrapper for listing blueprints in a project."""

    project_id: str
    blueprints: list[BlueprintListItem]


class BlueprintDetailResponse(BaseModel):
    """Full detail response for a single blueprint."""

    blueprint_id: str
    project_id: str
    original_filename: str
    file_extension: str
    file_size_bytes: int
    page_count: int
    page_images: list[BlueprintPage]
    is_pdf: bool
    uploaded_at: str
    metadata_path: str
    original_file_path: str
