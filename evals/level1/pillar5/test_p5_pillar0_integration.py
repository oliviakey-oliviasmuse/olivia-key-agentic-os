"""
Pillar 0 integration smoke tests for Pillar 5.
Tests run_weekly_drift_review() with P0 wiring active/inactive.
"""

import unittest
from unittest.mock import patch
from src.pillar5.drift_monitor import run_weekly_drift_review


class TestDriftMonitorIntegration(unittest.TestCase):

    def test_no_crash_without_p0(self):
        with patch("src.pillar5.drift_monitor._P0_AVAILABLE", False):
            result = run_weekly_drift_review()
        self.assertIsInstance(result, str)

    def test_no_crash_with_empty_feeds(self):
        with patch("src.pillar5.drift_monitor._P0_AVAILABLE", True), \
             patch("src.pillar5.drift_monitor._p0_weekly_review",
                   return_value="# Drift Report\n**Status: No breaches detected**"):
            result = run_weekly_drift_review(data_feeds={
                "content_log": [],
                "proposal_log": [],
                "delivery_log": [],
                "finance_log": [],
            })
        self.assertIsInstance(result, str)

    def test_no_crash_with_none_feeds(self):
        with patch("src.pillar5.drift_monitor._P0_AVAILABLE", True), \
             patch("src.pillar5.drift_monitor._p0_weekly_review",
                   return_value="# Drift Report\n**Status: No breaches detected**"):
            result = run_weekly_drift_review(None)
        self.assertIsInstance(result, str)

    def test_result_is_markdown(self):
        with patch("src.pillar5.drift_monitor._P0_AVAILABLE", True), \
             patch("src.pillar5.drift_monitor._p0_weekly_review",
                   return_value="# Drift Report\n**Status: ANDON — 1 breach**"):
            result = run_weekly_drift_review()
        self.assertIn("#", result)

    def test_breach_report_contains_status(self):
        breach_report = "# Drift Report\n**Status: ANDON — proposals below floor: 2**"
        with patch("src.pillar5.drift_monitor._P0_AVAILABLE", True), \
             patch("src.pillar5.drift_monitor._p0_weekly_review", return_value=breach_report):
            result = run_weekly_drift_review(data_feeds={"proposal_log": [{"amount": 1000}]})
        self.assertIn("ANDON", result)


if __name__ == "__main__":
    unittest.main()
