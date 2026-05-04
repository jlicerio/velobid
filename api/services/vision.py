"""Vision analysis service for blueprint MEP extraction using xAI Grok Vision."""

import base64
import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

XAI_API_KEY = os.getenv("XAI_API_KEY")
XAI_BASE_URL = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1")
XAI_VISION_MODEL = os.getenv("XAI_VISION_MODEL", "grok-2-vision-latest")

# Structured MEP takeoff schema prompt
ANALYSIS_PROMPT = """Extract MEP (Mechanical, Electrical, Plumbing) quantities and details from this construction blueprint page. List all:
- Equipment (AHUs, condensing units, fans, pumps)
- Ductwork sizes and lengths
- Pipe sizes and lengths
- Fixtures (diffusers, grilles, registers, lights, outlets)
- Room dimensions
- Any notes or callouts with quantities

Return as structured JSON with the following schema:
{
  "equipment": [{"name": string, "quantity": number, "notes": string}],
  "ductwork": [{"size": string, "length_ft": number, "notes": string}],
  "piping": [{"size": string, "length_ft": number, "type": string, "notes": string}],
  "fixtures": [{"name": string, "quantity": number, "location": string}],
  "rooms": [{"name": string, "dimensions": string, "area_sf": number}],
  "notes": [{"text": string}]
}

Include units where applicable. If a category has no items, return an empty array for that key.
"""


def encode_image(image_path: str) -> str:
    """Read an image file and return it as a base64-encoded string."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_analysis_sidecar_path(image_path: str) -> Path:
    """Given a blueprint page image path, return the path for the analysis JSON sidecar.

    Blueprint storage convention:
      {project_dir}/blueprints/{blueprint_id}/pages/page_01.png
    Sidecar output:
      {project_dir}/blueprints/{blueprint_id}/analysis_{page_num}.json

    Example:
        input:  .../blueprints/blueprint_001/pages/page_01.png
        output: .../blueprints/blueprint_001/analysis_1.json
    """
    img = Path(image_path)
    parent = img.parent.parent  # Go up from pages/ to blueprint dir
    stem = img.stem
    # Extract page number from stem like "page_01" or "page_1"
    parts = stem.split("_")
    if len(parts) >= 2 and parts[-1].isdigit():
        page_num = parts[-1].lstrip("0") or "0"
    else:
        page_num = "0"
    return parent / f"analysis_{page_num}.json"


def analyze_blueprint_page(
    image_path: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    custom_prompt: Optional[str] = None,
    timeout: int = 60,
) -> dict[str, Any]:
    """Analyze a single blueprint page image using xAI Grok Vision.

    Args:
        image_path: Path to the blueprint page image (PNG, JPEG, etc.)
        api_key: xAI API key (default: XAI_API_KEY env var)
        base_url: xAI API base URL (default: XAI_BASE_URL env var)
        model: Vision model name (default: XAI_VISION_MODEL env var)
        custom_prompt: Optional override for the analysis prompt
        timeout: Request timeout in seconds

    Returns:
        Structured MEP takeoff data as a dict matching the analysis schema.

    Raises:
        FileNotFoundError: If the image file doesn't exist
        ConnectionError: If the API call fails
        ValueError: If the API response can't be parsed
    """
    _api_key = api_key or XAI_API_KEY
    _base_url = base_url or XAI_BASE_URL
    _model = model or XAI_VISION_MODEL
    prompt = custom_prompt or ANALYSIS_PROMPT

    # Check if API key is configured
    if not _api_key:
        logger.warning("No XAI_API_KEY configured, returning mock analysis data")
        return _get_mock_analysis(image_path)

    # Encode the image
    logger.info("Encoding image: %s", image_path)
    b64_image = encode_image(image_path)

    # Determine media type from extension
    ext = Path(image_path).suffix.lower()
    media_type = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(ext, "image/png")

    # Build the OpenAI-compatible request
    url = f"{_base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": _model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{b64_image}"
                        },
                    },
                ],
            }
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
        "max_tokens": 4096,
    }

    logger.info("Calling xAI Vision API: %s at %s", _model, _base_url)
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        logger.error("xAI Vision API call failed: %s", exc)
        raise ConnectionError(f"Vision API request failed: {exc}") from exc

    # Parse the response
    try:
        data = resp.json()
        content = data["choices"][0]["message"]["content"].strip()
        # Handle possible markdown code fences
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:].strip()
        result = json.loads(content)
    except (KeyError, IndexError, json.JSONDecodeError) as exc:
        logger.error("Failed to parse Vision API response: %s", exc)
        logger.debug("Raw response: %s", resp.text[:1000])
        raise ValueError(f"Invalid API response format: {exc}") from exc

    # Validate the result has expected structure
    expected_keys = {"equipment", "ductwork", "piping", "fixtures", "rooms", "notes"}
    missing = expected_keys - set(result.keys())
    if missing:
        logger.warning("Analysis result missing expected keys: %s", missing)

    # Save sidecar
    sidecar_path = get_analysis_sidecar_path(image_path)
    try:
        sidecar_path.parent.mkdir(parents=True, exist_ok=True)
        with open(sidecar_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        logger.info("Analysis saved to: %s", sidecar_path)
    except OSError as exc:
        logger.error("Failed to save analysis sidecar: %s", exc)

    return result


def analyze_blueprint_pages(
    image_paths: list[str],
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    timeout: int = 60,
) -> dict[str, Any]:
    """Analyze multiple blueprint pages and merge results.

    For each page, calls analyze_blueprint_page. Merged results aggregate
    all arrays from each page into the combined output.

    Args:
        image_paths: List of paths to blueprint page images
        api_key, base_url, model, timeout: Passed through to analyze_blueprint_page

    Returns:
        Merged analysis results across all pages
    """
    merged: dict[str, Any] = {
        "equipment": [],
        "ductwork": [],
        "piping": [],
        "fixtures": [],
        "rooms": [],
        "notes": [],
        "_pages_analyzed": len(image_paths),
    }

    for img_path in image_paths:
        try:
            page_result = analyze_blueprint_page(
                image_path=img_path,
                api_key=api_key,
                base_url=base_url,
                model=model,
                timeout=timeout,
            )
            for key in ["equipment", "ductwork", "piping", "fixtures", "rooms", "notes"]:
                if key in page_result and isinstance(page_result[key], list):
                    merged.setdefault(key, []).extend(page_result[key])
        except (FileNotFoundError, ConnectionError, ValueError) as exc:
            logger.warning("Skipping page %s due to error: %s", img_path, exc)
            continue

    return merged


def detect_mep_symbols(image_path: str) -> dict[str, Any]:
    """Legacy alias for analyze_blueprint_page.

    Performs the same analysis but returns a symbol-focused summary.
    """
    result = analyze_blueprint_page(image_path)
    # Count total items across categories
    summary: dict[str, Any] = {"symbol_count": 0, "categories": {}}
    for cat in ["equipment", "ductwork", "piping", "fixtures"]:
        items = result.get(cat, [])
        count = sum(
            item.get("quantity", 1) if isinstance(item, dict) else 1
            for item in items
        )
        summary["categories"][cat] = {"count": count, "items": items}
        summary["symbol_count"] += count
    summary["rooms"] = result.get("rooms", [])
    summary["notes"] = result.get("notes", [])
    return summary


def _get_mock_analysis(image_path: str) -> dict[str, Any]:
    """Return mock analysis data when no API key is configured.

    This allows the endpoint to return useful data during development.
    """
    return {
        "equipment": [
            {"name": "Air Handling Unit (AHU-1)", "quantity": 1, "notes": "ROOF-1, 4000 CFM"},
            {"name": "Condensing Unit (CU-1)", "quantity": 1, "notes": "ROOF-1"},
            {"name": "Exhaust Fan (EF-1)", "quantity": 1, "notes": "RESTROOM"},
        ],
        "ductwork": [
            {"size": "24x12", "length_ft": 45, "notes": "Supply main"},
            {"size": "12 round", "length_ft": 30, "notes": "Return"},
        ],
        "piping": [
            {"size": "2", "length_ft": 60, "type": "Chilled Water Supply", "notes": ""},
            {"size": "2", "length_ft": 60, "type": "Chilled Water Return", "notes": ""},
            {"size": "3", "length_ft": 40, "type": "Condenser Water", "notes": ""},
        ],
        "fixtures": [
            {"name": "Supply Diffuser", "quantity": 12, "location": "Office area"},
            {"name": "Return Grille", "quantity": 4, "location": "Corridor"},
        ],
        "rooms": [
            {"name": "Office", "dimensions": "20' x 15'", "area_sf": 300},
            {"name": "Conference Room", "dimensions": "25' x 18'", "area_sf": 450},
        ],
        "notes": [
            {"text": "All ductwork to be SMACNA Class A"},
            {"text": "Insulate all chilled water piping with 1 closed cell"},
        ],
    }
