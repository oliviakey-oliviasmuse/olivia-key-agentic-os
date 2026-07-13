"""
Cross-pillar gate tests for P6 — P0 offer menu price floor (M2 soft flag on Invoice).
All tests must pass without a real P0 YAML — fail-open behaviour is verified directly.
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch
from src.pillar6.invoicing import Invoice


def _invoice(**kwargs):
    # Use a date 5 days ago so the invoice is still 'pending' (within Net 14 terms).
    # Hardcoded dates age out — relative dates keep tests stable.
    recent_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
    defaults = {
        "client_name": "Titan Aerospace",
        "engagement_name": "LSS Retainer",
        "invoice_date": recent_date,
        "amount": 25_000.0,
    }
    defaults.update(kwargs)
    return Invoice(**defaults)


class TestInvoiceDefectReasonField(unittest.TestCase):

    def test_defect_reason_defaults_to_none(self):
        inv = _invoice()
        self.assertIsNone(inv.defect_reason)

    def test_defect_reason_survives_post_init(self):
        """defect_reason is not wiped by _compute_status()."""
        inv = _invoice()
        self.assertIsNone(inv.defect_reason)
        inv.defect_reason = "below floor"
        self.assertEqual(inv.defect_reason, "below floor")


class TestCheckAgainstOfferMenuFailOpen(unittest.TestCase):

    def test_fail_open_when_p0_unavailable(self):
        inv = _invoice()
        with patch("src.pillar6.invoicing._P0_AVAILABLE", False):
            result = inv.check_against_offer_menu(yaml_path="/fake/menu.yaml")
        self.assertTrue(result["pass"])
        self.assertIn("fail-open", result["source"])
        self.assertEqual(inv.status, "pending")
        self.assertIsNone(inv.defect_reason)

    def test_fail_open_when_no_menu_supplied(self):
        """Neither menu object nor yaml_path → fail-open, invoice unchanged."""
        inv = _invoice()
        with patch("src.pillar6.invoicing._P0_AVAILABLE", True):
            result = inv.check_against_offer_menu()
        self.assertTrue(result["pass"])
        self.assertEqual(inv.status, "pending")
        self.assertIsNone(inv.defect_reason)


class TestCheckAgainstOfferMenuPass(unittest.TestCase):

    def test_pass_leaves_invoice_status_unchanged(self):
        inv = _invoice()
        floor_pass = {"pass": True, "reason": None, "source": "p0_offer_menu"}
        with patch("src.pillar6.invoicing._P0_AVAILABLE", True), \
             patch("src.pillar6.invoicing.check_price_floor", return_value=floor_pass):
            result = inv.check_against_offer_menu(yaml_path="/fake/menu.yaml")
        self.assertTrue(result["pass"])
        self.assertEqual(inv.status, "pending")
        self.assertIsNone(inv.defect_reason)

    def test_pass_with_live_menu_object(self):
        from unittest.mock import MagicMock
        floor_pass = {"pass": True, "reason": None, "source": "p0_offer_menu"}
        mock_menu = MagicMock()
        inv = _invoice()
        with patch("src.pillar6.invoicing._P0_AVAILABLE", True), \
             patch("src.pillar6.invoicing.check_price_floor", return_value=floor_pass) as mock_fn:
            inv.check_against_offer_menu(menu=mock_menu)
        mock_fn.assert_called_once_with(
            "LSS Retainer", 25_000.0, menu=mock_menu, yaml_path=None, mode="invoice"
        )


class TestCheckAgainstOfferMenuFail(unittest.TestCase):

    def test_fail_sets_status_to_defect(self):
        inv = _invoice()
        floor_fail = {
            "pass": False,
            "reason": "LSS Retainer floor is £30,000; invoiced £25,000",
            "source": "p0_offer_menu",
        }
        with patch("src.pillar6.invoicing._P0_AVAILABLE", True), \
             patch("src.pillar6.invoicing.check_price_floor", return_value=floor_fail):
            result = inv.check_against_offer_menu(yaml_path="/fake/menu.yaml")
        self.assertFalse(result["pass"])
        self.assertEqual(inv.status, "defect")
        self.assertIn("£30,000", inv.defect_reason)

    def test_fail_does_not_delete_invoice(self):
        """M2 is a soft flag — invoice is logged, not deleted."""
        inv = _invoice()
        floor_fail = {"pass": False, "reason": "below floor", "source": "p0_offer_menu"}
        with patch("src.pillar6.invoicing._P0_AVAILABLE", True), \
             patch("src.pillar6.invoicing.check_price_floor", return_value=floor_fail):
            inv.check_against_offer_menu(yaml_path="/fake/menu.yaml")
        # invoice data still intact
        self.assertEqual(inv.client_name, "Titan Aerospace")
        self.assertEqual(inv.amount, 25_000.0)
        self.assertEqual(inv.status, "defect")

    def test_fail_on_paid_invoice_does_not_revert_paid_status(self):
        """Paid invoices flagged retroactively should remain 'defect' (M2 overrides)."""
        inv = _invoice(paid_date="2026-06-28")
        self.assertEqual(inv.status, "paid")
        floor_fail = {"pass": False, "reason": "below floor", "source": "p0_offer_menu"}
        with patch("src.pillar6.invoicing._P0_AVAILABLE", True), \
             patch("src.pillar6.invoicing.check_price_floor", return_value=floor_fail):
            inv.check_against_offer_menu(yaml_path="/fake/menu.yaml")
        self.assertEqual(inv.status, "defect")

    def test_pass_on_paid_invoice_leaves_paid(self):
        inv = _invoice(paid_date="2026-06-28")
        floor_pass = {"pass": True, "reason": None, "source": "p0_offer_menu"}
        with patch("src.pillar6.invoicing._P0_AVAILABLE", True), \
             patch("src.pillar6.invoicing.check_price_floor", return_value=floor_pass):
            inv.check_against_offer_menu(yaml_path="/fake/menu.yaml")
        self.assertEqual(inv.status, "paid")

    def test_mode_is_invoice_not_proposal(self):
        """M2 check must use mode='invoice' (not 'proposal') to call the correct validation."""
        floor_pass = {"pass": True, "reason": None, "source": "p0_offer_menu"}
        inv = _invoice()
        with patch("src.pillar6.invoicing._P0_AVAILABLE", True), \
             patch("src.pillar6.invoicing.check_price_floor", return_value=floor_pass) as mock_fn:
            inv.check_against_offer_menu(yaml_path="/fake/menu.yaml")
        call_kwargs = mock_fn.call_args.kwargs
        self.assertEqual(call_kwargs.get("mode"), "invoice")


class TestExistingTestsStillPass(unittest.TestCase):
    """Smoke test — defect_reason field must not break existing invoice behaviour."""

    def test_pending_invoice_gate_still_fires(self):
        with self.assertRaises(ValueError):
            Invoice(client_name="", engagement_name="X", invoice_date="2026-06-27", amount=1000)

    def test_amount_gate_still_fires(self):
        with self.assertRaises(ValueError):
            Invoice(client_name="C", engagement_name="X", invoice_date="2026-06-27", amount=-1)

    def test_normal_invoice_still_works(self):
        inv = _invoice()
        self.assertEqual(inv.status, "pending")
        self.assertIsNone(inv.defect_reason)


if __name__ == "__main__":
    unittest.main()
