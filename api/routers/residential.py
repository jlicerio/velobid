"""API routes for residential HVAC estimates."""

import json
import re
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException

from api.schemas.residential import (
    ResidentialEstimateRequest,
    ResidentialEstimateResponse,
)
from bid_engine.residential.pricing import price_residential_estimate
from bid_engine.residential.templates.proposal import generate_residential_proposal

router = APIRouter(prefix="/api/v1/residential", tags=["residential"])

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
PROJECTS_DIR = CONFIG_DIR / "projects"
BID_PROJECTS_DIR = PROJECT_ROOT / "bid_projects"
RESIDENTIAL_OUTPUT_DIR = BID_PROJECTS_DIR / "residential"


def _project_id(name: str) -> str:
    """Convert a name to a snake_case project ID."""
    return re.sub(r"[^a-z0-9_]", "", name.lower().replace(" ", "_"))


@router.post("/estimate", response_model=ResidentialEstimateResponse, status_code=201)
def create_residential_estimate(request: ResidentialEstimateRequest):
    """Create a residential HVAC estimate and optionally generate a proposal PDF."""
    # Price it
    result = price_residential_estimate(
        equipment=[e.model_dump() for e in request.equipment],
        labor_tasks=[t.model_dump() for t in request.labor_tasks],
        misc_materials=request.misc_materials,
        permit_fee=request.permit_fee,
        equipment_markup_pct=request.equipment_markup_pct,
        labor_rate=request.labor_rate,
    )

    # Save project config
    project_id = _project_id(request.customer_name + "_" + datetime.now().strftime("%m%d%y"))
    project_config = {
        "project_type": "residential",
        "name": f"{request.customer_name} - HVAC Estimate",
        "customer_name": request.customer_name,
        "customer_address": request.customer_address,
        "customer_phone": request.customer_phone,
        "customer_email": request.customer_email,
        "property_sqft": request.property_sqft,
        "scope_description": request.scope_description,
        "equipment": [e.model_dump() for e in request.equipment],
        "labor_tasks": [t.model_dump() for t in request.labor_tasks],
        "pricing": result["totals"],
        "status": "estimate",
        "archived": False,
        "created_at": datetime.now().isoformat(),
    }
    project_path = PROJECTS_DIR / f"{project_id}.json"
    if project_path.exists():
        project_id = project_id + "_" + datetime.now().strftime("%H%M%S")
        project_path = PROJECTS_DIR / f"{project_id}.json"
    project_config["id"] = project_id
    with project_path.open("w", encoding="utf-8") as f:
        json.dump(project_config, f, indent=2)

    # Generate PDF
    pdf_url = None
    if request.generate_pdf:
        try:
            output_dir = RESIDENTIAL_OUTPUT_DIR / project_id
            output_dir.mkdir(parents=True, exist_ok=True)
            pdf_path = output_dir / "proposal.pdf"
            generate_residential_proposal(
                output_path=str(pdf_path),
                project_name=project_config["name"],
                customer_name=request.customer_name,
                customer_address=request.customer_address,
                customer_phone=request.customer_phone or "",
                scope_description=request.scope_description,
                equipment_list=[e.model_dump() for e in request.equipment],
                labor_list=[t.model_dump() for t in request.labor_tasks],
                totals=result["totals"],
                proposal_date=datetime.now().strftime("%B %d, %Y"),
            )
            pdf_url = f"/files/residential/{project_id}/proposal.pdf"
        except Exception as e:
            # PDF generation failed but estimate is still valid
            pdf_url = None

    return ResidentialEstimateResponse(
        project_id=project_id,
        customer_name=request.customer_name,
        grand_total=result["totals"]["grand_total"],
        pdf_url=pdf_url,
        totals=result["totals"],
        line_items=result["line_items"],
    )


@router.get("/estimates")
def list_residential_estimates():
    """List all residential estimates."""
    results = []
    for path in sorted(PROJECTS_DIR.glob("*.json")):
        try:
            with path.open(encoding="utf-8-sig") as f:
                data = json.load(f)
            if data.get("project_type") == "residential":
                totals = data.get("pricing", {})
                results.append({
                    "id": path.stem,
                    "customer_name": data.get("customer_name", ""),
                    "total": totals.get("grand_total", 0),
                    "status": data.get("status", "estimate"),
                    "created_at": data.get("created_at", ""),
                    "archived": data.get("archived", False),
                })
        except Exception:
            continue
    return results
