from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from app.services.cache import get_revenue_summary
from app.services.revenue_rules import require_tenant_id
from app.core.auth import authenticate_request as get_current_user

router = APIRouter()

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    year: int = 2024,
    month: int = 3,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    try:
        tenant_id = require_tenant_id(current_user)
    except ValueError:
        raise HTTPException(status_code=403, detail="Tenant context is required")
    if month < 1 or month > 12:
        raise HTTPException(status_code=422, detail="month must be between 1 and 12")

    revenue_data = await get_revenue_summary(property_id, tenant_id, year, month)
    
    total_revenue_float = float(revenue_data['total'])
    
    return {
        "property_id": revenue_data['property_id'],
        "total_revenue": total_revenue_float,
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count']
    }
