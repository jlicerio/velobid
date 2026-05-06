"""Service layer for blueprint upload, storage, and retrieval."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO

from api.schemas.blueprints import (
    BlueprintDetailResponse,
    BlueprintListItem,
    BlueprintListResponse,
    BlueprintPage,
    BlueprintUploadResponse,
)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BID_PROJECTS_DIR = PROJECT_ROOT / "bid_projects"
BLUEPRINTS_ROOT = Path("/data/velobid/blueprints")

MAX_FILE_SIZE = 50 * 1024 * 1024
ALLOWED_EXTENSIONS = frozenset({".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif"})


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def _is_allowed(filename: str) -> bool:
    return _extension(filename) in ALLOWED_EXTENSIONS


def _is_pdf(filename: str) -> bool:
    return _extension(filename) == ".pdf"


def _blueprint_dir(project_id: str, blueprint_id: str) -> Path:
    return BLUEPRINTS_ROOT / project_id / "blueprints" / blueprint_id


def _pages_dir(blueprint_dir: Path) -> Path:
    pages = blueprint_dir / "pages"
    _ensure_dir(pages)
    return pages


def _metadata_path(blueprint_dir: Path) -> Path:
    return blueprint_dir / "metadata.json"


def _original_path(blueprint_dir: Path, filename: str) -> Path:
    return blueprint_dir / filename


def _rel_path(path: Path) -> str:
    return str(path.relative_to(BLUEPRINTS_ROOT)).replace("\\", "/")


def _url_path(path: Path) -> str:
    return f"/files/{_rel_path(path)}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_blueprint(project_id: str, filename: str, file_obj: BinaryIO) -> BlueprintUploadResponse:
    if not _is_allowed(filename):
        raise ValueError(
            f"File type not allowed: {filename}. "
            f"Accepted: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    raw = file_obj.read()
    if len(raw) > MAX_FILE_SIZE:
        raise ValueError(
            f"File exceeds maximum allowed size of 50 MB "
            f"({len(raw)} bytes uploaded)."
        )

    blueprint_id = uuid.uuid4().hex[:12]
    ext = _extension(filename)
    is_pdf_flag = ext == ".pdf"
    upload_ts = _now_iso()

    bdir = _ensure_dir(_blueprint_dir(project_id, blueprint_id))
    orig_path = _original_path(bdir, f"original{ext}")

    orig_path.write_bytes(raw)

    page_images: list[BlueprintPage] = []
    page_count = 1

    if is_pdf_flag:
        try:
            from pdf2image import convert_from_path

            pdir = _pages_dir(bdir)
            pil_images = convert_from_path(str(orig_path), fmt="png")

            for idx, pil_img in enumerate(pil_images, start=1):
                page_filename = f"page_{idx:04d}.png"
                page_path = pdir / page_filename
                pil_img.save(str(page_path), "PNG")

                width, height = pil_img.size
                page_images.append(
                    BlueprintPage(
                        page_number=idx,
                        filename=page_filename,
                        path=_rel_path(page_path),
                        url=_url_path(page_path),
                        width=width,
                        height=height,
                    )
                )

            page_count = len(pil_images)
        except Exception:
            page_count = 0
    else:
        page_images.append(
            BlueprintPage(
                page_number=1,
                filename=orig_path.name,
                path=_rel_path(orig_path),
                url=_url_path(orig_path),
                width=None,
                height=None,
            )
        )

    meta = {
        "blueprint_id": blueprint_id,
        "project_id": project_id,
        "original_filename": filename,
        "file_extension": ext,
        "file_size_bytes": len(raw),
        "page_count": page_count,
        "is_pdf": is_pdf_flag,
        "uploaded_at": upload_ts,
        "original_file_path": _rel_path(orig_path),
        "page_images": [
            {
                "page_number": p.page_number,
                "filename": p.filename,
                "path": p.path,
                "url": p.url,
                "width": p.width,
                "height": p.height,
            }
            for p in page_images
        ],
    }

    meta_path = _metadata_path(bdir)
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return BlueprintUploadResponse(
        blueprint_id=blueprint_id,
        project_id=project_id,
        original_filename=filename,
        file_extension=ext,
        file_size_bytes=len(raw),
        page_count=page_count,
        page_images=page_images,
        is_pdf=is_pdf_flag,
        uploaded_at=upload_ts,
        metadata_path=_rel_path(meta_path),
    )


def list_blueprints(project_id: str) -> BlueprintListResponse:
    blueprints_dir = BLUEPRINTS_ROOT / project_id / "blueprints"
    items: list[BlueprintListItem] = []

    if not blueprints_dir.is_dir():
        return BlueprintListResponse(project_id=project_id, blueprints=items)

    for bp_dir in sorted(blueprints_dir.iterdir()):
        if not bp_dir.is_dir():
            continue
        meta_path = _metadata_path(bp_dir)
        if not meta_path.is_file():
            continue

        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        items.append(
            BlueprintListItem(
                blueprint_id=meta.get("blueprint_id", bp_dir.name),
                project_id=meta.get("project_id", project_id),
                original_filename=meta.get("original_filename", "unknown"),
                file_extension=meta.get("file_extension", ""),
                file_size_bytes=meta.get("file_size_bytes", 0),
                page_count=meta.get("page_count", 0),
                is_pdf=meta.get("is_pdf", False),
                uploaded_at=meta.get("uploaded_at", ""),
            )
        )

    items.sort(key=lambda x: x.uploaded_at, reverse=True)
    return BlueprintListResponse(project_id=project_id, blueprints=items)


def get_blueprint(project_id: str, blueprint_id: str) -> BlueprintDetailResponse:
    bp_dir = _blueprint_dir(project_id, blueprint_id)
    if not bp_dir.is_dir():
        raise FileNotFoundError(f"Blueprint not found: {blueprint_id}")

    meta_path = _metadata_path(bp_dir)
    if not meta_path.is_file():
        raise FileNotFoundError(f"Metadata missing for blueprint: {blueprint_id}")

    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    page_images = [
        BlueprintPage(
            page_number=p["page_number"],
            filename=p["filename"],
            path=p["path"],
            url=p["url"],
            width=p.get("width"),
            height=p.get("height"),
        )
        for p in meta.get("page_images", [])
    ]

    orig_filename = meta.get("original_filename", "unknown")
    ext = meta.get("file_extension", "")
    orig_rel = meta.get("original_file_path", "")
    orig_abs = BLUEPRINTS_ROOT / orig_rel if orig_rel else bp_dir / f"original{ext}"

    return BlueprintDetailResponse(
        blueprint_id=meta.get("blueprint_id", blueprint_id),
        project_id=meta.get("project_id", project_id),
        original_filename=orig_filename,
        file_extension=ext,
        file_size_bytes=meta.get("file_size_bytes", 0),
        page_count=meta.get("page_count", 0),
        page_images=page_images,
        is_pdf=meta.get("is_pdf", False),
        uploaded_at=meta.get("uploaded_at", ""),
        metadata_path=_rel_path(meta_path),
        original_file_path=_rel_path(orig_abs),
    )
