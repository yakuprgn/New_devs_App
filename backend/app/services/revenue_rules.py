from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Tuple
from zoneinfo import ZoneInfo

MONEY_QUANTUM = Decimal("0.01")


def revenue_cache_key(tenant_id: str, property_id: str, year: int, month: int) -> str:
    """Build a tenant-isolated cache key for a monthly revenue summary."""
    return f"revenue:v2:{tenant_id}:{property_id}:{year}:{month:02d}"


def require_tenant_id(user: Any) -> str:
    """Return the authenticated tenant or reject a missing tenant context."""
    tenant_id = getattr(user, "tenant_id", None)
    if not tenant_id:
        raise ValueError("Tenant context is required")
    return tenant_id


def monthly_utc_bounds(year: int, month: int, timezone_name: str) -> Tuple[datetime, datetime]:
    """Return half-open UTC bounds for a calendar month in a property's timezone."""
    if month < 1 or month > 12:
        raise ValueError("month must be between 1 and 12")
    property_tz = ZoneInfo(timezone_name)
    start_local = datetime(year, month, 1, tzinfo=property_tz)
    if month == 12:
        end_local = datetime(year + 1, 1, 1, tzinfo=property_tz)
    else:
        end_local = datetime(year, month + 1, 1, tzinfo=property_tz)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


def round_money(value: Any) -> Decimal:
    """Round monetary values to cents without introducing binary floats."""
    return Decimal(str(value or "0")).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)
