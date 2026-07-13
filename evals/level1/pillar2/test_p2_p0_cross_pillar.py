"""
Cross-pillar gate tests for P2 — G18 (voice rules, P0 A3) and G19 (channel authority, P0 A6).
All tests must pass without a real P0 YAML file — fail-open behaviour is verified directly.
"""

import unittest
from unittest.mock import patch, MagicMock
from src.pillar2.content_gate import (
    check_g18_voice_rules,
    check_g19_channel_authority,
    run_programmatic_gates,
    aggregate_verdict,
    ANDON_GATES,
    DEFECT_CODES,
    GateResult,
)


# --- helpers ---

def _pass_gate(gate_id: str) -> GateResult:
    return GateResult(gate_id, True, "ok")


def _fail_gate(gate_id: str, defect: str = "M00") -> GateResult:
    return GateResult(gate_id, False, "fail", defect)


class TestAndonAndDefectConfig(unittest.TestCase):
    def test_g19_is_andon_gate(self):
        self.assertIn("G19", ANDON_GATES)

    def test_g18_is_not_andon_gate(self):
        self.assertNotIn("G18", ANDON_GATES)

    def test_m12_in_defect_codes(self):
        self.assertIn("M12", DEFECT_CODES)
        self.assertIn("G18", DEFECT_CODES["M12"])

    def test_m13_in_defect_codes(self):
        self.assertIn("M13", DEFECT_CODES)
        self.assertIn("G19", DEFECT_CODES["M13"])


class TestG18VoiceRules(unittest.TestCase):

    def test_fail_open_when_p0_unavailable(self):
        with patch("src.pillar2.content_gate._P0_AVAILABLE", False):
            result = check_g18_voice_rules("any text")
        self.assertTrue(result.passed)
        self.assertEqual(result.gate, "G18")
        self.assertIn("fail-open", result.reason.lower())

    def test_fail_open_when_no_positioning_supplied(self):
        """No yaml_path and no positioning object → pass (fail-open)."""
        result = check_g18_voice_rules("any text")
        self.assertTrue(result.passed)

    def test_pass_when_p0_returns_pass(self):
        mock_result = {"pass": True, "violations": [], "source": "p0_voice"}
        with patch("src.pillar2.content_gate._P0_AVAILABLE", True), \
             patch("src.pillar2.content_gate.check_voice_compliance", return_value=mock_result):
            result = check_g18_voice_rules("clean content", yaml_path="/fake/path.yaml")
        self.assertTrue(result.passed)
        self.assertEqual(result.gate, "G18")

    def test_fail_when_p0_returns_violations(self):
        mock_result = {"pass": False, "violations": ["best-in-class", "world-class"], "source": "p0_voice"}
        with patch("src.pillar2.content_gate._P0_AVAILABLE", True), \
             patch("src.pillar2.content_gate.check_voice_compliance", return_value=mock_result):
            result = check_g18_voice_rules("we are the best-in-class world-class firm", yaml_path="/fake/path.yaml")
        self.assertFalse(result.passed)
        self.assertEqual(result.gate, "G18")
        self.assertEqual(result.defect_code, "M12")
        self.assertIn("best-in-class", result.reason)

    def test_live_positioning_object_bypasses_file_load(self):
        mock_positioning = MagicMock()
        mock_result = {"pass": True, "violations": [], "source": "p0_voice"}
        with patch("src.pillar2.content_gate._P0_AVAILABLE", True), \
             patch("src.pillar2.content_gate.check_voice_compliance", return_value=mock_result) as mock_fn:
            check_g18_voice_rules("text", positioning=mock_positioning)
        mock_fn.assert_called_once_with("text", positioning=mock_positioning, yaml_path=None)


class TestG19ChannelAuthority(unittest.TestCase):

    def test_fail_open_when_p0_unavailable(self):
        with patch("src.pillar2.content_gate._P0_AVAILABLE", False):
            result = check_g19_channel_authority("LinkedIn", {})
        self.assertTrue(result.passed)
        self.assertEqual(result.gate, "G19")
        self.assertIn("fail-open", result.reason.lower())

    def test_fail_open_when_no_distribution_supplied(self):
        result = check_g19_channel_authority("LinkedIn", {})
        self.assertTrue(result.passed)

    def test_donotbother_channel_fails(self):
        allowed_result = {"allowed": False, "donotbother": True, "primary": False, "source": "p0_distribution"}
        with patch("src.pillar2.content_gate._P0_AVAILABLE", True), \
             patch("src.pillar2.content_gate.check_channel_allowed", return_value=allowed_result):
            result = check_g19_channel_authority("TikTok", {}, dist_yaml_path="/fake/dist.yaml")
        self.assertFalse(result.passed)
        self.assertEqual(result.gate, "G19")
        self.assertEqual(result.defect_code, "M13")
        self.assertIn("do-not-bother", result.reason)

    def test_unapproved_channel_fails(self):
        allowed_result = {"allowed": False, "donotbother": False, "primary": False, "source": "p0_distribution"}
        with patch("src.pillar2.content_gate._P0_AVAILABLE", True), \
             patch("src.pillar2.content_gate.check_channel_allowed", return_value=allowed_result):
            result = check_g19_channel_authority("Reddit", {}, dist_yaml_path="/fake/dist.yaml")
        self.assertFalse(result.passed)
        self.assertEqual(result.defect_code, "M13")
        self.assertIn("not in P0 distribution authority", result.reason)

    def test_format_violation_fails(self):
        allowed_result = {"allowed": True, "donotbother": False, "primary": True, "source": "p0_distribution"}
        fmt_result = {"pass": False, "violations": ["max_length exceeded"], "source": "p0_distribution"}
        with patch("src.pillar2.content_gate._P0_AVAILABLE", True), \
             patch("src.pillar2.content_gate.check_channel_allowed", return_value=allowed_result), \
             patch("src.pillar2.content_gate.validate_channel_content", return_value=fmt_result):
            result = check_g19_channel_authority("LinkedIn", {"text": "x" * 4000}, dist_yaml_path="/fake/dist.yaml")
        self.assertFalse(result.passed)
        self.assertEqual(result.defect_code, "M13")
        self.assertIn("max_length exceeded", result.reason)

    def test_approved_primary_channel_passes(self):
        allowed_result = {"allowed": True, "donotbother": False, "primary": True, "source": "p0_distribution"}
        fmt_result = {"pass": True, "violations": [], "source": "p0_distribution"}
        with patch("src.pillar2.content_gate._P0_AVAILABLE", True), \
             patch("src.pillar2.content_gate.check_channel_allowed", return_value=allowed_result), \
             patch("src.pillar2.content_gate.validate_channel_content", return_value=fmt_result):
            result = check_g19_channel_authority("LinkedIn", {"text": "good post"}, dist_yaml_path="/fake/dist.yaml")
        self.assertTrue(result.passed)
        self.assertIn("primary", result.reason)

    def test_approved_secondary_channel_passes(self):
        allowed_result = {"allowed": True, "donotbother": False, "primary": False, "source": "p0_distribution"}
        fmt_result = {"pass": True, "violations": [], "source": "p0_distribution"}
        with patch("src.pillar2.content_gate._P0_AVAILABLE", True), \
             patch("src.pillar2.content_gate.check_channel_allowed", return_value=allowed_result), \
             patch("src.pillar2.content_gate.validate_channel_content", return_value=fmt_result):
            result = check_g19_channel_authority("Substack", {"text": "good newsletter"}, dist_yaml_path="/fake/dist.yaml")
        self.assertTrue(result.passed)
        self.assertIn("secondary", result.reason)

    def test_g19_failure_triggers_andon_in_aggregate(self):
        """G19 failure must trigger ANDON STOP in aggregate_verdict (tuple return)."""
        results = [
            _pass_gate("G2"), _pass_gate("G5"), _pass_gate("G17"),
            _fail_gate("G19", "M13"),
        ]
        verdict, pass_rate, defects = aggregate_verdict(results)
        self.assertEqual(verdict, "ANDON STOP")


class TestRunProgrammaticGatesIntegration(unittest.TestCase):

    def _good_text(self):
        return (
            "Reduce CoPQ by eliminating scrap in your weld cell. "
            "Backed by our £2.4M recovery at Tier 1 aerospace supplier — "
            "data verified against OEE logs. "
            "Book a free 30-min diagnostic call to see if this applies to your plant."
        )

    def test_g18_not_run_without_p0_config(self):
        results = run_programmatic_gates(
            self._good_text(), "Hygiene", "brand_awareness"
        )
        gate_ids = [r.gate for r in results]
        self.assertNotIn("G18", gate_ids)

    def test_g19_not_run_without_channel(self):
        results = run_programmatic_gates(
            self._good_text(), "Hygiene", "brand_awareness"
        )
        gate_ids = [r.gate for r in results]
        self.assertNotIn("G19", gate_ids)

    def test_g18_runs_when_positioning_yaml_supplied(self):
        mock_result = {"pass": True, "violations": [], "source": "p0_voice"}
        with patch("src.pillar2.content_gate._P0_AVAILABLE", True), \
             patch("src.pillar2.content_gate.check_voice_compliance", return_value=mock_result):
            results = run_programmatic_gates(
                self._good_text(), "Hygiene", "brand_awareness",
                p0_positioning_yaml="/fake/positioning.yaml",
            )
        gate_ids = [r.gate for r in results]
        self.assertIn("G18", gate_ids)

    def test_g19_runs_when_channel_supplied(self):
        allowed = {"allowed": True, "donotbother": False, "primary": True, "source": "p0_distribution"}
        fmt = {"pass": True, "violations": [], "source": "p0_distribution"}
        with patch("src.pillar2.content_gate._P0_AVAILABLE", True), \
             patch("src.pillar2.content_gate.check_channel_allowed", return_value=allowed), \
             patch("src.pillar2.content_gate.validate_channel_content", return_value=fmt):
            results = run_programmatic_gates(
                self._good_text(), "Hygiene", "brand_awareness",
                channel="LinkedIn",
                p0_distribution_yaml="/fake/dist.yaml",
            )
        gate_ids = [r.gate for r in results]
        self.assertIn("G19", gate_ids)


if __name__ == "__main__":
    unittest.main()
