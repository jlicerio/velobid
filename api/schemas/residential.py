"""Pydantic schemas for residential HVAC estimates."""

from typing import Optional

from pydantic import BaseModel, Field


class EquipmentItem(BaseModel):
    """A piece of equipment in a residential estimate."""

    item: str = Field(..., examples=["Condensing Unit"])
    brand: str = Field("Trane", examples=["Trane", "Carrier", "Rheem"])
    model: str = Field("", examples=["4TTR4036"])
    tons: Optional[float] = None
    btu: Optional[int] = None
    cost: float = Field(..., examples=[1200.0])
    qty: int = 1


class LaborTask(BaseModel):
    """A labor task in a residential estimate."""

    item: str = Field(..., examples=["Remove old equipment"])
    hours: float = Field(..., examples=[4.0])
    qty: int = 1


class ResidentialEstimateRequest(BaseModel):
    """Request to create a residential HVAC estimate."""

    customer_name: str = Field(..., examples=["John Smith"])
    customer_address: str = Field(..., examples=["123 Main St, McAllen TX"])
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    property_sqft: Optional[float] = None
    scope_description: str = Field(..., examples=["Replace existing 4-ton split system"])
    equipment: list[EquipmentItem] = []
    labor_tasks: list[LaborTask] = []
    misc_materials: float = 0
    permit_fee: Optional[float] = None
    equipment_markup_pct: Optional[float] = None
    labor_rate: Optional[float] = None
    generate_pdf: bool = True


class ResidentialEstimateResponse(BaseModel):
    """Response from creating a residential estimate."""

    project_id: str
    customer_name: str
    grand_total: float
    pdf_url: Optional[str] = None
    totals: dict
    line_items: list[dict]
