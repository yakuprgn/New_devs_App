from typing import Dict, Any

from fastapi import HTTPException
from app.services.revenue_rules import monthly_utc_bounds, round_money

async def calculate_total_revenue(
    property_id: str, tenant_id: str, year: int = 2024, month: int = 3
) -> Dict[str, Any]:
    """
    Aggregates revenue from database.
    """
    try:
        from app.core.database_pool import db_pool

        await db_pool.initialize()
        
        if db_pool.session_factory:
            async with db_pool.get_session() as session:
                # Use SQLAlchemy text for raw SQL
                from sqlalchemy import text
                
                property_query = text("""
                    SELECT timezone
                    FROM properties
                    WHERE id = :property_id AND tenant_id = :tenant_id
                """)
                property_result = await session.execute(property_query, {
                    "property_id": property_id,
                    "tenant_id": tenant_id,
                })
                property_row = property_result.fetchone()
                if not property_row:
                    raise HTTPException(status_code=404, detail="Property not found")

                start_date, end_date = monthly_utc_bounds(
                    year, month, property_row.timezone
                )

                query = text("""
                    SELECT 
                        property_id,
                        SUM(total_amount) as total_revenue,
                        COUNT(*) as reservation_count
                    FROM reservations 
                    WHERE property_id = :property_id
                      AND tenant_id = :tenant_id
                      AND check_in_date >= :start_date
                      AND check_in_date < :end_date
                    GROUP BY property_id
                """)
                
                result = await session.execute(query, {
                    "property_id": property_id, 
                    "tenant_id": tenant_id,
                    "start_date": start_date,
                    "end_date": end_date,
                })
                row = result.fetchone()
                
                if row:
                    total_revenue = round_money(row.total_revenue)
                    return {
                        "property_id": property_id,
                        "tenant_id": tenant_id,
                        "total": format(total_revenue, ".2f"),
                        "currency": "USD", 
                        "count": row.reservation_count
                    }
                else:
                    # No reservations found for this property
                    return {
                        "property_id": property_id,
                        "tenant_id": tenant_id,
                        "total": "0.00",
                        "currency": "USD",
                        "count": 0
                    }
        else:
            raise Exception("Database pool not available")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error for {property_id} (tenant: {tenant_id}): {e}")
        
        # Never substitute global property-based mock data here: property IDs
        # can overlap between tenants, so doing so can disclose another
        # tenant's financial figures during an outage.
        raise HTTPException(status_code=503, detail="Revenue data is unavailable")
