"""
Cross-pillar gate tests for P3 — P0 ICP hard reject (gatekeeper) and P0 price floor (proposal).
All tests must pass without a real P0 YAML — fail-open behaviour is verified directly.
"""

import unittest
from unittest.mock import patch
from src.pillar3.gatekeeper import score_prospect
from src.pillar3.proposal_builder import build_proposal


# --- fixtures ---

def _good_agent2():
    return {
        "client_name": "Titan Aerospace",
        "date": "2026-06-27",
        "copq_total": 10_000_000,
        "copq_table": [],
        "business_case_pass": True,
    }


def _good_pricing():
    return {"monthly_fee": 25_000, "annual_fee": 150_000, "fee_basis": "15% recovery"}


def _good_failure_modes():
    return [
        {"mode": "Low buy-in", "severity": 6, "occurrence": 5, "detection": 3},
        {"mode": "Scope creep", "severity": 5, "occurrence": 4, "detection": 4},
        {"mode": "Data gaps", "severity": 4, "occurrence": 4, "detection": 5},
    ]


# ───────────────────────────────────────────────
# Gatekeeper — P0 ICP hard reject
# ───────────────────────────────────────────────

class TestP0IcpHardReject(unittest.TestCase):

    def test_score_proceed_without_p0_config(self):
        """No p0_yaml_path → P0 check skipped, normal rubric runs."""
        result = score_prospect(role=5, company_size=5, industry=5, pain_awareness=4, budget_authority=4)
        self.assertEqual(result["verdict"], "PROCEED")
        self.assertNotIn("p0_reject", result)

    def test_fail_open_when_p0_unavailable(self):
        """P0 import fails → _P0_AVAILABLE=False → normal scoring continues."""
        with patch("src.pillar3.gatekeeper._P0_AVAILABLE", False):
            result = score_prospect(
                role=5, company_size=5, industry=5, pain_awareness=4, budget_authority=4,
                p0_yaml_path="/fake/positioning.yaml",
            )
        self.assertEqual(result["verdict"], "PROCEED")
        self.assertNotIn("p0_reject", result)

    def test_p0_reject_overrides_high_rubric_score(self):
        """Even a perfect rubric score (25/25) is hard-rejected when P0 ICP fails."""
        icp_fail = {"pass": False, "reason": "industry not in ICP: Consumer FMCG", "source": "p0_icp"}
        with patch("src.pillar3.gatekeeper._P0_AVAILABLE", True), \
             patch("src.pillar3.gatekeeper.check_icp_membership", return_value=icp_fail):
            result = score_prospect(
                role=5, company_size=5, industry=5, pain_awareness=5, budget_authority=5,
                p0_yaml_path="/fake/positioning.yaml",
            )
        self.assertEqual(result["verdict"], "REJECT")
        self.assertTrue(result.get("p0_reject"))
        self.assertIsNone(result["score"])
        self.assertIn("Consumer FMCG", result["justification"]["p0_icp"])

    def test_p0_pass_allows_normal_scoring(self):
        """P0 ICP pass → rubric runs normally → PROCEED on high score."""
        icp_pass = {"pass": True, "reason": None, "source": "p0_icp"}
        with patch("src.pillar3.gatekeeper._P0_AVAILABLE", True), \
             patch("src.pillar3.gatekeeper.check_icp_membership", return_value=icp_pass):
            result = score_prospect(
                role=5, company_size=5, industry=5, pain_awareness=4, budget_authority=4,
                p0_yaml_path="/fake/positioning.yaml",
            )
        self.assertEqual(result["verdict"], "PROCEED")
        self.assertNotIn("p0_reject", result)

    def test_p0_reject_has_null_copq(self):
        """Hard-reject result must not include a CoPQ estimate (no partial data)."""
        icp_fail = {"pass": False, "reason": "role not in ICP", "source": "p0_icp"}
        with patch("src.pillar3.gatekeeper._P0_AVAILABLE", True), \
             patch("src.pillar3.gatekeeper.check_icp_membership", return_value=icp_fail):
            result = score_prospect(
                role=3, company_size=3, industry=3,
                revenue=50_000_000,
                p0_yaml_path="/fake/positioning.yaml",
            )
        self.assertEqual(result["verdict"], "REJECT")
        self.assertIsNone(result["copq_estimate"])

    def test_p0_icp_check_receives_available_fields_only(self):
        """Only non-None fields are passed to check_icp_membership."""
        icp_pass = {"pass": True, "reason": None, "source": "p0_icp"}
        with patch("src.pillar3.gatekeeper._P0_AVAILABLE", True), \
             patch("src.pillar3.gatekeeper.check_icp_membership", return_value=icp_pass) as mock_fn:
            score_prospect(
                role=5, industry=4,  # company_size omitted
                pain_awareness=3, budget_authority=3,
                p0_yaml_path="/fake/positioning.yaml",
            )
        call_kwargs = mock_fn.call_args
        prospect_data = call_kwargs.args[0] if call_kwargs.args else call_kwargs.kwargs.get("prospect_data", {})
        self.assertNotIn("company_size", prospect_data)
        self.assertIn("industry", prospect_data)


# ───────────────────────────────────────────────
# Proposal builder — P0 price floor
# ───────────────────────────────────────────────

class TestP0PriceFloor(unittest.TestCase):

    def test_proposal_builds_without_p0_config(self):
        """No p0_menu_yaml → P0 price floor skipped, proposal builds normally."""
        result = build_proposal(
            _good_agent2(), _good_pricing(), _good_failure_modes(), 150_000
        )
        self.assertIn("Proposal", result)

    def test_fail_open_when_p0_unavailable(self):
        """P0 import fails → _P0_AVAILABLE=False → price floor skipped."""
        with patch("src.pillar3.proposal_builder._P0_AVAILABLE", False):
            result = build_proposal(
                _good_agent2(), _good_pricing(), _good_failure_modes(), 150_000,
                p0_menu_yaml="/fake/menu.yaml", offer_name="LSS Retainer",
            )
        self.assertIn("Proposal", result)

    def test_price_below_floor_raises_error(self):
        """Fee below P0 price floor → ValueError with M1 code."""
        floor_fail = {"pass": False, "reason": "LSS Retainer floor is £30,000/month; proposed £25,000", "source": "p0_offer_menu"}
        with patch("src.pillar3.proposal_builder._P0_AVAILABLE", True), \
             patch("src.pillar3.proposal_builder.check_price_floor", return_value=floor_fail):
            with self.assertRaises(ValueError) as ctx:
                build_proposal(
                    _good_agent2(), _good_pricing(), _good_failure_modes(), 150_000,
                    p0_menu_yaml="/fake/menu.yaml", offer_name="LSS Retainer",
                )
        self.assertIn("M1", str(ctx.exception))
        self.assertIn("£30,000", str(ctx.exception))

    def test_price_above_floor_builds_proposal(self):
        """Fee above P0 price floor → proposal builds normally."""
        floor_pass = {"pass": True, "reason": None, "source": "p0_offer_menu"}
        with patch("src.pillar3.proposal_builder._P0_AVAILABLE", True), \
             patch("src.pillar3.proposal_builder.check_price_floor", return_value=floor_pass):
            result = build_proposal(
                _good_agent2(), _good_pricing(), _good_failure_modes(), 150_000,
                p0_menu_yaml="/fake/menu.yaml", offer_name="LSS Retainer",
            )
        self.assertIn("Proposal", result)

    def test_price_floor_uses_monthly_fee(self):
        """check_price_floor is called with the monthly_fee from pricing dict."""
        floor_pass = {"pass": True, "reason": None, "source": "p0_offer_menu"}
        with patch("src.pillar3.proposal_builder._P0_AVAILABLE", True), \
             patch("src.pillar3.proposal_builder.check_price_floor", return_value=floor_pass) as mock_fn:
            build_proposal(
                _good_agent2(), _good_pricing(), _good_failure_modes(), 150_000,
                p0_menu_yaml="/fake/menu.yaml", offer_name="LSS Retainer",
            )
        mock_fn.assert_called_once()
        call_args = mock_fn.call_args
        self.assertEqual(call_args.args[0], "LSS Retainer")
        self.assertEqual(call_args.args[1], 25_000)

    def test_price_floor_skipped_when_no_offer_name(self):
        """If offer_name is None, price floor gate is skipped (no P0 call)."""
        with patch("src.pillar3.proposal_builder._P0_AVAILABLE", True), \
             patch("src.pillar3.proposal_builder.check_price_floor") as mock_fn:
            build_proposal(
                _good_agent2(), _good_pricing(), _good_failure_modes(), 150_000,
                p0_menu_yaml="/fake/menu.yaml",
                # offer_name not supplied
            )
        mock_fn.assert_not_called()


if __name__ == "__main__":
    unittest.main()
