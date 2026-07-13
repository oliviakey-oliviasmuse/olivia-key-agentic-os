import unittest
from src.pillar3.gatekeeper import (
    score_prospect,
    score_icp_rubric,
    map_scorecard_to_icp,
    estimate_copq,
    THRESHOLD_COLD,
    THRESHOLD_WARM,
    DEFER_MIN,
    MAX_ICP_SCORE,
)

class TestDiscoveryGatekeeper(unittest.TestCase):

    def test_icp_rubric_full(self):
        total, scores = score_icp_rubric(5, 4, 5, 5, 5)
        self.assertEqual(total, 24)
        self.assertEqual(scores["role"], 5)

    def test_scorecard_mapping(self):
        # Fixed: map_scorecard_to_icp now returns int, not float
        # 20 × (25/24) = 20.833 → rounds to 21
        mapped = map_scorecard_to_icp(20)
        self.assertEqual(mapped, 21)
        self.assertIsInstance(mapped, int)

    def test_copq_estimate(self):
        est = estimate_copq(200_000_000)
        self.assertAlmostEqual(est["central"], 30_000_000)
        self.assertAlmostEqual(est["low"], 24_000_000)
        self.assertAlmostEqual(est["high"], 36_000_000)

    def test_proceed_cold(self):
        result = score_prospect(
            role=5, company_size=5, industry=5, pain_awareness=5, budget_authority=5,
            warm_lead=False, revenue=100_000_000,
        )
        self.assertEqual(result["verdict"], "PROCEED")
        self.assertGreaterEqual(result["score"], THRESHOLD_COLD)

    def test_defer_cold(self):
        result = score_prospect(
            role=3, company_size=3, industry=3, pain_awareness=3, budget_authority=3,
            warm_lead=False,
        )
        # Fixed: assert on result["score"], not a hardcoded local variable
        self.assertGreaterEqual(result["score"], DEFER_MIN)
        self.assertLess(result["score"], THRESHOLD_COLD)
        self.assertEqual(result["verdict"], "DEFER")

    def test_reject_cold(self):
        result = score_prospect(
            role=1, company_size=1, industry=0, pain_awareness=1, budget_authority=0,
            warm_lead=False,
        )
        # Fixed: assert on result["score"], not a hardcoded local variable
        self.assertLess(result["score"], DEFER_MIN)
        self.assertEqual(result["verdict"], "REJECT")

    def test_warm_override(self):
        result = score_prospect(
            role=3, company_size=3, industry=3, pain_awareness=3, budget_authority=3,
            warm_lead=True,
        )
        # Fixed: assert on result["score"], not a hardcoded local variable
        self.assertGreaterEqual(result["score"], THRESHOLD_WARM)
        self.assertLess(result["score"], THRESHOLD_COLD)
        self.assertEqual(result["verdict"], "PROCEED")

    def test_scorecard_bridge(self):
        # Fixed: expect int 21, not float 20.8
        result = score_prospect(scorecard_total=20, warm_lead=False, revenue=100_000_000)
        self.assertEqual(result["verdict"], "PROCEED")
        self.assertEqual(result["score"], 21)
        self.assertIsInstance(result["score"], int)

    def test_missing_data_below_g1_threshold(self):
        # Fixed: G1 now requires ≥3 attributes, not all 5.
        # 2 populated → INSUFFICIENT_DATA.
        result = score_prospect(
            role=5, company_size=5,
            industry=None, pain_awareness=None, budget_authority=None,
        )
        self.assertEqual(result["verdict"], "INSUFFICIENT_DATA")
        self.assertIn("industry", result["missing_fields"])
        self.assertIn("pain_awareness", result["missing_fields"])
        self.assertIn("budget_authority", result["missing_fields"])

    def test_3_fields_populated_passes_g1(self):
        # 3 populated → G1 passes → verdict is not INSUFFICIENT_DATA
        result = score_prospect(
            role=5, company_size=5, industry=5,
            pain_awareness=None, budget_authority=None,
        )
        self.assertNotEqual(result["verdict"], "INSUFFICIENT_DATA")
        self.assertIn("pain_awareness", result["missing_fields"])
        self.assertIn("budget_authority", result["missing_fields"])

    def test_copq_estimate_optional(self):
        result = score_prospect(
            role=5, company_size=5, industry=5, pain_awareness=5, budget_authority=5,
            revenue=200_000_000,
        )
        self.assertIsNotNone(result["copq_estimate"])
        self.assertAlmostEqual(result["copq_estimate"]["central"], 30_000_000)

    # --- Boundary tests (18 / 17 / 14 / 8 / 7) ---

    def test_boundary_cold_proceed(self):
        # 4+4+4+3+3 = 18 → exactly cold PROCEED threshold
        result = score_prospect(
            role=4, company_size=4, industry=4, pain_awareness=3, budget_authority=3,
            warm_lead=False,
        )
        self.assertEqual(result["score"], 18)
        self.assertEqual(result["verdict"], "PROCEED")

    def test_boundary_cold_defer_upper(self):
        # 4+4+4+3+2 = 17 → one below cold PROCEED
        result = score_prospect(
            role=4, company_size=4, industry=4, pain_awareness=3, budget_authority=2,
            warm_lead=False,
        )
        self.assertEqual(result["score"], 17)
        self.assertEqual(result["verdict"], "DEFER")

    def test_boundary_cold_defer_lower(self):
        # 2+2+2+1+1 = 8 → exactly DEFER lower boundary
        result = score_prospect(
            role=2, company_size=2, industry=2, pain_awareness=1, budget_authority=1,
            warm_lead=False,
        )
        self.assertEqual(result["score"], 8)
        self.assertEqual(result["verdict"], "DEFER")

    def test_boundary_cold_reject(self):
        # 2+2+2+0+1 = 7 → one below DEFER lower boundary
        result = score_prospect(
            role=2, company_size=2, industry=2, pain_awareness=0, budget_authority=1,
            warm_lead=False,
        )
        self.assertEqual(result["score"], 7)
        self.assertEqual(result["verdict"], "REJECT")

    def test_boundary_warm_proceed(self):
        # 3+3+3+3+2 = 14 → exactly warm PROCEED threshold
        result = score_prospect(
            role=3, company_size=3, industry=3, pain_awareness=3, budget_authority=2,
            warm_lead=True,
        )
        self.assertEqual(result["score"], 14)
        self.assertEqual(result["verdict"], "PROCEED")

    def test_warm_defer(self):
        # 2+2+2+2+2 = 10 → warm DEFER (8–13)
        result = score_prospect(
            role=2, company_size=2, industry=2, pain_awareness=2, budget_authority=2,
            warm_lead=True,
        )
        self.assertEqual(result["score"], 10)
        self.assertEqual(result["verdict"], "DEFER")

if __name__ == "__main__":
    unittest.main()
