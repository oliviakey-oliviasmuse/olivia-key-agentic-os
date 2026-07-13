"""
Pillar 0 integration smoke tests for Pillar 6.
Tests Invoice with P0 offer menu wiring.
"""

import unittest
from unittest.mock import patch
from src.pillar6.invoicing import Invoice


def _invoice(**kwargs):
    defaults = {
        "client_name": "Titan Aerospace",
        "engagement_name": "LSS Retainer",
        "invoice_date": "2026-06-27",
        "amount": 25_000.0,
    }
    defaults.update(kwargs)
    return Invoice(**defaults)


class TestInvoicePillar0Integration(unittest.TestCase):

    def test_invoice_creation_no_crash_without_p0(self):
        inv = _invoice()
        self.assertIsNotNone(inv.status)
        self.assertIn(inv.status, ("pending", "paid", "overdue", "defect"))

    def test_defect_reason_none_without_p0(self):
        inv = _invoice()
        self.assertIsNone(inv.defect_reason)

    def test_check_against_offer_menu_returns_dict(self):
        floor_pass = {"pass": True, "reason": None, "source": "p0_offer_menu"}
        inv = _invoice()
        with patch("src.pillar6.invoicing._P0_AVAILABLE", True), \
             patch("src.pillar6.invoicing.check_price_floor", return_value=floor_pass):
            result = inv.check_against_offer_menu(yaml_path="/fake/menu.yaml")
        self.assertIn("pass", result)
        self.assertTrue(result["pass"])

    def test_below_floor_invoice_sets_defect(self):
        floor_fail = {
            "pass": False,
            "reason": "LSS Retainer floor is £30,000; invoiced £25,000",
            "source": "p0_offer_menu",
        }
        inv = _invoice()
        with patch("src.pillar6.invoicing._P0_AVAILABLE", True), \
             patch("src.pillar6.invoicing.check_price_floor", return_value=floor_fail):
            inv.check_against_offer_menu(yaml_path="/fake/menu.yaml")
        self.assertEqual(inv.status, "defect")
        self.assertIsNotNone(inv.defect_reason)
        self.assertIn("£30,000", inv.defect_reason)

    def test_invoice_fields_survive_defect_flag(self):
        """M2 is soft — invoice data is not lost when flagged as defect."""
        floor_fail = {"pass": False, "reason": "below floor", "source": "p0_offer_menu"}
        inv = _invoice()
        with patch("src.pillar6.invoicing._P0_AVAILABLE", True), \
             patch("src.pillar6.invoicing.check_price_floor", return_value=floor_fail):
            inv.check_against_offer_menu(yaml_path="/fake/menu.yaml")
        self.assertEqual(inv.client_name, "Titan Aerospace")
        self.assertEqual(inv.engagement_name, "LSS Retainer")
        self.assertEqual(inv.amount, 25_000.0)


if __name__ == "__main__":
    unittest.main()
