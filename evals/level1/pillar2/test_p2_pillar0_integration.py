"""
Pillar 0 integration smoke tests for Pillar 2.
Tests check_gates() with P0 wiring active/inactive — no crash, correct dict shape.
"""

import unittest
from unittest.mock import patch
from src.pillar2.content_gate import check_gates


_GOOD_TEXT = (
    "Reduce CoPQ by eliminating scrap in your weld cell. "
    "Backed by our £2.4M recovery at Tier 1 aerospace supplier — "
    "data verified against OEE logs. "
    "Book a free 30-min diagnostic call to see if this applies to your plant."
)

_BAD_TEXT = "This revolutionary, game-changing product is the best."


class TestCheckGatesShape(unittest.TestCase):

    def test_returns_required_keys(self):
        result = check_gates(_GOOD_TEXT, {"tier": "Hygiene", "commercial_objective": "brand_awareness"})
        for key in ("pass", "failed_gates", "defects", "andon_fired", "pass_rate", "predicted_engagement"):
            self.assertIn(key, result)

    def test_pass_is_bool(self):
        result = check_gates(_GOOD_TEXT, {"tier": "Hygiene", "commercial_objective": "brand_awareness"})
        self.assertIsInstance(result["pass"], bool)

    def test_andon_fired_on_hype_word(self):
        result = check_gates(_BAD_TEXT, {"tier": "Hub", "commercial_objective": "enquiries"})
        self.assertTrue(result["andon_fired"])
        self.assertFalse(result["pass"])

    def test_pass_rate_between_0_and_1(self):
        result = check_gates(_GOOD_TEXT, {"tier": "Hygiene", "commercial_objective": "brand_awareness"})
        self.assertGreaterEqual(result["pass_rate"], 0.0)
        self.assertLessEqual(result["pass_rate"], 1.0)

    def test_failed_gates_is_list(self):
        result = check_gates(_GOOD_TEXT, {"tier": "Hygiene", "commercial_objective": "brand_awareness"})
        self.assertIsInstance(result["failed_gates"], list)


class TestCheckGatesG18G19Wiring(unittest.TestCase):

    def test_no_p0_options_no_g18_g19(self):
        result = check_gates(_GOOD_TEXT, {"tier": "Hygiene", "commercial_objective": "brand_awareness"})
        self.assertNotIn("G18", result["failed_gates"])
        self.assertNotIn("G19", result["failed_gates"])

    def test_voice_violation_adds_g18_to_failed(self):
        mock_result = {"pass": False, "violations": ["world-class"], "source": "p0_voice"}
        with patch("src.pillar2.content_gate._P0_AVAILABLE", True), \
             patch("src.pillar2.content_gate.check_voice_compliance", return_value=mock_result):
            result = check_gates(
                _GOOD_TEXT,
                {"tier": "Hygiene", "commercial_objective": "brand_awareness", "p0_positioning_yaml": "/fake/pos.yaml"},
            )
        self.assertIn("G18", result["failed_gates"])
        self.assertFalse(result["pass"])

    def test_donotbother_channel_triggers_andon(self):
        allowed = {"allowed": False, "donotbother": True, "primary": False, "source": "p0_distribution"}
        fmt = {"pass": True, "violations": [], "source": "p0_distribution"}
        with patch("src.pillar2.content_gate._P0_AVAILABLE", True), \
             patch("src.pillar2.content_gate.check_channel_allowed", return_value=allowed), \
             patch("src.pillar2.content_gate.validate_channel_content", return_value=fmt):
            result = check_gates(
                _GOOD_TEXT,
                {"tier": "Hygiene", "commercial_objective": "brand_awareness", "channel": "TikTok"},
            )
        self.assertTrue(result["andon_fired"])
        self.assertIn("G19", result["failed_gates"])


if __name__ == "__main__":
    unittest.main()
