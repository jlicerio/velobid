from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from api.services.profile_manager import create_bidder_profile

router = APIRouter(prefix="/api/v1/admin/bidders", tags=["admin"])


class CreateBidderProfileRequest(BaseModel):
    company_name: str
    trades: list[str]
    company_context: str = ""
    default_labor_rate: float = 65.0
    default_equipment_markup_pct: float = 10.0
    default_overhead_profit_pct: float = 15.0
    default_contingency_pct: float = 5.0
    default_tax_rate: float = 0.0825
    service_area: str = "Nationwide"


class ProfileResponse(BaseModel):
    profile_name: str
    status: str
    message: str = ""


@router.post("/{bidder_id}/profile", response_model=ProfileResponse)
async def create_profile(bidder_id: str, req: CreateBidderProfileRequest):
    try:
        result = create_bidder_profile(
            bidder_id=bidder_id,
            company_name=req.company_name,
            trades=req.trades,
            company_context=req.company_context,
            default_labor_rate=req.default_labor_rate,
            default_equipment_markup_pct=req.default_equipment_markup_pct,
            default_overhead_profit_pct=req.default_overhead_profit_pct,
            default_contingency_pct=req.default_contingency_pct,
            default_tax_rate=req.default_tax_rate,
            service_area=req.service_area,
        )
        return ProfileResponse(
            profile_name=result["profile_name"],
            status=result["status"],
            message=f"Hermes profile created for {req.company_name}",
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
