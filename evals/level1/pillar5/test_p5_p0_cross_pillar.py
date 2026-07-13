"""
Cross-pillar tests — Pillar 5 drift monitor → Pillar 0 drift detector wiring.
"""

import unittest
from unittest.mock import patch
from src.pillar5.drift_monitor import run_weekly_drift_review


class TestDriftMonitorFailOpen(unittest.TestCase):

    def test_returns_string_without_p0(self):
        with patch("src.pillar5.drift_monitor._P0_AVAILABLE", False):
            result = run_weekly_drift_review()
        self.assertIsInstance(result, str)
        self.assertIn("Pillar 0 not available", result)

    def test_fail_open_accepts_none(self):
        with patch("src.pillar5.drift_monitor._P0_AVAILABLE", False):
            result = run_weekly_drift_review(None)
        self.assertIsInstance(result, str)

    def test_fail_open_accepts_empty_dict(self):
        with patch("src.pillar5.drift_monitor._P0_AVAILABLE", False):
            result = run_weekly_drift_review({})
        self.assertIsInstance(result, str)


class TestDriftMonitorWithP0(unittest.TestCase):

    def _mock_report(self, *args, **kwargs):
        return "# Drift Report\n**Status: No breaches detected**"

    def test_calls_p0_weekly_review(self):
        with patch("src.pillar5.drift_monitor._P0_AVAILABLE", True), \
             patch("src.pillar5.drift_monitor._p0_weekly_review", side_effect=self._mock_report) as mock_fn:
            result = run_weekly_drift_review()
        mock_fn.assert_called_once()
        self.assertIsInstance(result, str)

    def test_passes_data_feeds_through(self):
        feeds = {"content_log": [{"violations": 2}], "proposal_log": [], "delivery_log": [], "finance_log": []}
        with patch("src.pillar5.drift_monitor._P0_AVAILABLE", True), \
             patch("src.pillar5.drift_monitor._p0_weekly_review", return_value="# Drift Report") as mock_fn:
            run_weekly_drift_review(feeds)
        call_kwargs = mock_fn.call_args
        self.assertIsNotNone(call_kwargs)

    def test_returns_markdown_string(self):
        with patch("src.pillar5.drift_monitor._P0_AVAILABLE", True), \
             patch("src.pillar5.drift_monitor._p0_weekly_review", return_value="# Drift Report\n**Status: ANDON**"):
            result = run_weekly_drift_review()
        self.assertIn("Drift Report", result)

    def test_none_data_feeds_uses_defaults(self):
        with patch("src.pillar5.drift_monitor._P0_AVAILABLE", True), \
             patch("src.pillar5.drift_monitor._p0_weekly_review", side_effect=self._mock_report) as mock_fn:
            run_weekly_drift_review(None)
        mock_fn.assert_called_once()

    def test_empty_dict_data_feeds_normalised(self):
        with patch("src.pillar5.drift_monitor._P0_AVAILABLE", True), \
             patch("src.pillar5.drift_monitor._p0_weekly_review", side_effect=self._mock_report) as mock_fn:
            run_weekly_drift_review({})
        mock_fn.assert_called_once()


if __name__ == "__main__":
    unittest.main()
