"""
Pillar 0 integration smoke tests for Pillar 3.
Tests recommend() with P0 ICP wiring and run_weekly_drift_review().
"""

import unittest
from unittest.mock import patch
from src.pillar3.scorecard import recommend, RECOMMENDATION_REJECT, RECOMMENDATION_PROCEED


class TestRecommendIcpGate(unittest.TestCase):

    def test_recommend_without_icp_data_uses_rubric(self):
        verdict, reason = recommend(total=20)
        self.assertEqual(verdict, RECOMMENDATION_PROCEED)

    def test_recommend_with_icp_data_fails_open_when_p0_unavailable(self):
        with patch("src.pillar3.scorecard._P0_AVAILABLE", False):
            verdict, reason = recommend(
                total=20, industry="Consumer FMCG", company_size=50
            )
        self.assertEqual(verdict, RECOMMENDATION_PROCEED)

    def test_recommend_icp_reject_overrides_high_score(self):
        icp_fail = {"pass": False, "reason": "industry not in ICP", "source": "p0_icp"}
        with patch("src.pillar3.scorecard._P0_AVAILABLE", True), \
             patch("src.pillar3.scorecard.validate_prospect", return_value=icp_fail):
            verdict, reason = recommend(
                total=24, industry="Consumer FMCG", company_size=50
            )
        self.assertEqual(verdict, RECOMMENDATION_REJECT)
        self.assertIn("P0 ICP", reason)

    def test_recommend_icp_pass_allows_proceed(self):
        icp_pass = {"pass": True, "reason": None, "source": "p0_icp"}
        with patch("src.pillar3.scorecard._P0_AVAILABLE", True), \
             patch("src.pillar3.scorecard.validate_prospect", return_value=icp_pass):
            verdict, reason = recommend(
                total=20, industry="Aerospace", company_size=500
            )
        self.assertEqual(verdict, RECOMMENDATION_PROCEED)

    def test_recommend_skips_icp_when_industry_missing(self):
        """Only company_size, no industry → P0 gate skipped."""
        with patch("src.pillar3.scorecard._P0_AVAILABLE", True), \
             patch("src.pillar3.scorecard.validate_prospect") as mock_fn:
            recommend(total=20, company_size=500)
        mock_fn.assert_not_called()

    def test_recommend_skips_icp_when_company_size_missing(self):
        """Only industry, no company_size → P0 gate skipped."""
        with patch("src.pillar3.scorecard._P0_AVAILABLE", True), \
             patch("src.pillar3.scorecard.validate_prospect") as mock_fn:
            recommend(total=20, industry="Aerospace")
        mock_fn.assert_not_called()

    def test_verdict_str_in_valid_set(self):
        verdict, reason = recommend(total=15, industry="Aerospace", company_size=500)
        self.assertIn(verdict, ("PROCEED", "DEFER", "REJECT"))


class TestDriftReviewRunner(unittest.TestCase):

    def test_run_weekly_drift_review_no_crash(self):
        try:
            from src.pillar0.drift_detector_generator import run_weekly_drift_review
            result = run_weekly_drift_review()
            self.assertIsInstance(result, str)
            self.assertIn("Drift", result)
        except ImportError:
            self.skipTest("P0 drift detector not available from this repo path")

    def test_run_weekly_drift_review_with_empty_feeds(self):
        try:
            from src.pillar0.drift_detector_generator import run_weekly_drift_review
            result = run_weekly_drift_review(data_feeds={
                "content_log": [],
                "proposal_log": [],
                "delivery_log": [],
                "finance_log": [],
            })
            self.assertIsInstance(result, str)
        except ImportError:
            self.skipTest("P0 drift detector not available from this repo path")


if __name__ == "__main__":
    unittest.main()
