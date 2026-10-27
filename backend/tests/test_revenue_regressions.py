import unittest
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from app.services.revenue_rules import (
    monthly_utc_bounds,
    require_tenant_id,
    revenue_cache_key,
    round_money,
)


class RevenueRegressionTests(unittest.TestCase):
    def test_revenue_cache_keys_are_isolated_by_tenant_and_month(self):
        tenant_a = revenue_cache_key("tenant-a", "prop-001", 2024, 3)
        tenant_b = revenue_cache_key("tenant-b", "prop-001", 2024, 3)

        self.assertEqual(tenant_a, "revenue:v2:tenant-a:prop-001:2024:03")
        self.assertEqual(tenant_b, "revenue:v2:tenant-b:prop-001:2024:03")
        self.assertNotEqual(tenant_a, tenant_b)
        self.assertNotEqual(
            tenant_a, revenue_cache_key("tenant-a", "prop-001", 2024, 4)
        )

    def test_authenticated_tenant_context_is_required(self):
        with self.assertRaisesRegex(ValueError, "Tenant context is required"):
            require_tenant_id(SimpleNamespace(tenant_id=None))

        self.assertEqual(
            require_tenant_id(SimpleNamespace(tenant_id="tenant-b")), "tenant-b"
        )

    def test_paris_march_bounds_include_local_midnight_reservation(self):
        start, end = monthly_utc_bounds(2024, 3, "Europe/Paris")

        self.assertEqual(start, datetime(2024, 2, 29, 23, 0, tzinfo=timezone.utc))
        self.assertEqual(end, datetime(2024, 3, 31, 22, 0, tzinfo=timezone.utc))
        reservation = datetime(2024, 2, 29, 23, 30, tzinfo=timezone.utc)
        self.assertTrue(start <= reservation < end)

    def test_new_york_march_bounds_handle_dst_and_half_open_end(self):
        start, end = monthly_utc_bounds(2024, 3, "America/New_York")

        self.assertEqual(start, datetime(2024, 3, 1, 5, 0, tzinfo=timezone.utc))
        self.assertEqual(end, datetime(2024, 4, 1, 4, 0, tzinfo=timezone.utc))
        self.assertFalse(start <= end < end)

    def test_financial_aggregation_and_rounding_are_decimal_based(self):
        amounts = [Decimal("333.333"), Decimal("333.333"), Decimal("333.334")]

        self.assertEqual(round_money(sum(amounts)), Decimal("1000.00"))
        self.assertEqual(round_money(Decimal("10.005")), Decimal("10.01"))
        self.assertEqual(round_money(Decimal("10.004")), Decimal("10.00"))

    def test_month_validation(self):
        with self.assertRaises(ValueError):
            monthly_utc_bounds(2024, 13, "UTC")


if __name__ == "__main__":
    unittest.main()
