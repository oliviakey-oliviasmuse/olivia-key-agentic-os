import unittest
from datetime import datetime, timedelta
from src.pillar0.distribution import (
    FormatRules,
    Channel,
    DistributionAuthority,
    to_yaml,
    from_yaml,
)


def _make_channel(
    name="LinkedIn",
    min_per_week=1,
    max_per_day=1,
    max_length=3000,
    required_elements=None,
    is_primary=True,
    is_secondary=False,
):
    rules = FormatRules(
        max_length=max_length,
        required_elements=required_elements or ["hook"],
    )
    return Channel(
        name=name,
        format_rules=rules,
        cadence_min_per_week=min_per_week,
        cadence_max_per_day=max_per_day,
        is_primary=is_primary,
        is_secondary=is_secondary,
    )


def _days_ago(n):
    return (datetime.now() - timedelta(days=n)).strftime("%Y-%m-%d")


def _today():
    return datetime.now().strftime("%Y-%m-%d")


class TestChannel(unittest.TestCase):
    def test_valid_channel(self):
        channel = _make_channel()
        self.assertEqual(channel.name, "LinkedIn")
        self.assertEqual(channel.cadence_min_per_week, 1)
        self.assertEqual(channel.cadence_max_per_day, 1)

    def test_g2_missing_name(self):
        with self.assertRaises(ValueError) as ctx:
            _make_channel(name="")
        self.assertIn("G2", str(ctx.exception))

    def test_g2_negative_cadence_min(self):
        with self.assertRaises(ValueError) as ctx:
            _make_channel(min_per_week=-1)
        self.assertIn("G2", str(ctx.exception))

    def test_g2_negative_cadence_max(self):
        with self.assertRaises(ValueError) as ctx:
            _make_channel(max_per_day=-1)
        self.assertIn("G2", str(ctx.exception))

    def test_g3_invalid_cadence_ratio(self):
        # min_per_week=10 > max_per_day=1 * 7 = 7 → G3 error
        with self.assertRaises(ValueError) as ctx:
            _make_channel(min_per_week=10, max_per_day=1)
        self.assertIn("G3", str(ctx.exception))

    def test_g3_boundary_valid(self):
        # min=7, max_per_day=1 → 7 == 1*7 → valid (not strictly greater)
        channel = _make_channel(min_per_week=7, max_per_day=1)
        self.assertEqual(channel.cadence_min_per_week, 7)

    def test_cadence_max_per_day_zero_means_no_cap(self):
        # 0 max_per_day = no daily cap; G3 should not fire
        channel = _make_channel(min_per_week=1, max_per_day=0)
        self.assertEqual(channel.cadence_max_per_day, 0)

    def test_zero_min_per_week_valid(self):
        channel = _make_channel(min_per_week=0, max_per_day=1)
        self.assertEqual(channel.cadence_min_per_week, 0)

    def test_format_rules_stored(self):
        channel = _make_channel(max_length=500, required_elements=["hook", "CTA"])
        self.assertEqual(channel.format_rules.max_length, 500)
        self.assertIn("CTA", channel.format_rules.required_elements)

    def test_secondary_channel_flag(self):
        channel = _make_channel(is_primary=False, is_secondary=True)
        self.assertFalse(channel.is_primary)
        self.assertTrue(channel.is_secondary)


class TestDistributionAuthority(unittest.TestCase):
    def setUp(self):
        self.primary = _make_channel(name="LinkedIn", min_per_week=1, max_per_day=1)
        self.secondary = _make_channel(
            name="Substack", min_per_week=1, max_per_day=1,
            is_primary=False, is_secondary=True,
        )
        self.distribution = DistributionAuthority(
            primary_channels=[self.primary],
            secondary_channels=[self.secondary],
            donotbother_channels=["TikTok", "YouTube"],
        )

    def test_g1_empty_primary_raises(self):
        with self.assertRaises(ValueError) as ctx:
            DistributionAuthority(primary_channels=[])
        self.assertIn("G1", str(ctx.exception))

    def test_get_all_channels(self):
        all_ch = self.distribution.get_all_channels()
        self.assertEqual(len(all_ch), 2)
        names = [c.name for c in all_ch]
        self.assertIn("LinkedIn", names)
        self.assertIn("Substack", names)

    def test_get_primary(self):
        primary = self.distribution.get_primary()
        self.assertEqual(len(primary), 1)
        self.assertEqual(primary[0].name, "LinkedIn")

    def test_get_secondary(self):
        secondary = self.distribution.get_secondary()
        self.assertEqual(len(secondary), 1)
        self.assertEqual(secondary[0].name, "Substack")

    def test_is_allowed_primary(self):
        self.assertTrue(self.distribution.is_allowed("LinkedIn"))

    def test_is_allowed_secondary(self):
        self.assertTrue(self.distribution.is_allowed("Substack"))

    def test_is_allowed_unapproved(self):
        self.assertFalse(self.distribution.is_allowed("TikTok"))

    def test_is_primary_true(self):
        self.assertTrue(self.distribution.is_primary_channel("LinkedIn"))

    def test_is_primary_false_for_secondary(self):
        self.assertFalse(self.distribution.is_primary_channel("Substack"))

    def test_is_secondary_true(self):
        self.assertTrue(self.distribution.is_secondary_channel("Substack"))

    def test_is_secondary_false_for_primary(self):
        self.assertFalse(self.distribution.is_secondary_channel("LinkedIn"))

    def test_is_donotbother_true(self):
        self.assertTrue(self.distribution.is_donotbother("TikTok"))

    def test_is_donotbother_false(self):
        self.assertFalse(self.distribution.is_donotbother("LinkedIn"))


class TestValidateContent(unittest.TestCase):
    def setUp(self):
        self.primary = _make_channel(
            name="LinkedIn",
            max_length=3000,
            required_elements=["hook", "CTA"],
        )
        self.distribution = DistributionAuthority(primary_channels=[self.primary])

    def test_validate_content_pass(self):
        content = {"text": "This hook grabs attention. Find out more. CTA: click here."}
        result = self.distribution.validate_content("LinkedIn", content)
        self.assertTrue(result["pass"])
        self.assertEqual(result["violations"], [])

    def test_validate_content_fail_length(self):
        content = {"text": "a" * 4000}
        result = self.distribution.validate_content("LinkedIn", content)
        self.assertFalse(result["pass"])
        self.assertTrue(any("exceeds max" in v for v in result["violations"]))

    def test_validate_content_fail_missing_required_element(self):
        # Text has CTA but no "hook"
        content = {"text": "Nothing relevant here. CTA: click here."}
        result = self.distribution.validate_content("LinkedIn", content)
        self.assertFalse(result["pass"])
        self.assertIn("Missing required element: 'hook'", result["violations"][0])

    def test_validate_content_fail_multiple_violations(self):
        # Too long AND missing both elements
        content = {"text": "x" * 4000}
        result = self.distribution.validate_content("LinkedIn", content)
        self.assertFalse(result["pass"])
        self.assertGreater(len(result["violations"]), 1)

    def test_validate_content_channel_not_found(self):
        content = {"text": "Test"}
        result = self.distribution.validate_content("TikTok", content)
        self.assertFalse(result["pass"])
        self.assertIn("not found", result["reason"])

    def test_validate_content_case_insensitive_element_match(self):
        # required element "hook" should match "HOOK" in text
        content = {"text": "HOOK — this is the opening. CTA: read more."}
        result = self.distribution.validate_content("LinkedIn", content)
        self.assertTrue(result["pass"])

    def test_validate_content_secondary_channel_checked(self):
        secondary = _make_channel(
            name="Substack",
            max_length=5000,
            required_elements=["intro"],
            is_primary=False,
            is_secondary=True,
        )
        dist = DistributionAuthority(
            primary_channels=[self.primary],
            secondary_channels=[secondary],
        )
        content = {"text": "intro section here"}
        result = dist.validate_content("Substack", content)
        self.assertTrue(result["pass"])


class TestCheckCadence(unittest.TestCase):
    def setUp(self):
        self.channel = _make_channel(name="LinkedIn", min_per_week=1, max_per_day=1)
        self.distribution = DistributionAuthority(primary_channels=[self.channel])

    def test_cadence_ok(self):
        post_log = [_days_ago(i) for i in range(1, 5)]  # 4 posts in last 7 days, min=1
        result = self.distribution.check_cadence("LinkedIn", post_log)
        self.assertEqual(result["status"], "OK")
        self.assertIn("On track", result["reason"])

    def test_cadence_andon_below_minimum(self):
        # Channel with min=3, only 2 posts → ANDON
        channel = _make_channel(name="X", min_per_week=3, max_per_day=2)
        dist = DistributionAuthority(primary_channels=[channel])
        post_log = [_days_ago(1), _days_ago(2)]  # 2 posts, min=3
        result = dist.check_cadence("X", post_log)
        self.assertEqual(result["status"], "ANDON")
        self.assertIn("Only 2 posts", result["reason"])

    def test_cadence_andon_no_posts(self):
        result = self.distribution.check_cadence("LinkedIn", [])
        self.assertEqual(result["status"], "ANDON")
        self.assertIn("No posts logged", result["reason"])

    def test_cadence_warning_max_per_day_exceeded(self):
        # 2 posts today, max_per_day=1 → WARNING
        post_log = [_today(), _today(), _days_ago(1)]  # 3 in 7 days but 2 today
        result = self.distribution.check_cadence("LinkedIn", post_log)
        self.assertEqual(result["status"], "WARNING")
        self.assertIn("2 posts today", result["reason"])

    def test_cadence_channel_not_found(self):
        result = self.distribution.check_cadence("TikTok", [])
        self.assertEqual(result["status"], "ERROR")
        self.assertIn("not found", result["reason"])

    def test_cadence_ok_min_zero(self):
        # min=0 means no minimum, empty log → OK
        channel = _make_channel(name="Archive", min_per_week=0, max_per_day=1)
        dist = DistributionAuthority(primary_channels=[channel])
        result = dist.check_cadence("Archive", [])
        self.assertEqual(result["status"], "OK")

    def test_cadence_old_posts_not_counted(self):
        # Posts older than 7 days don't count toward weekly minimum
        post_log = [_days_ago(8), _days_ago(9), _days_ago(10)]
        channel = _make_channel(name="LinkedIn", min_per_week=1, max_per_day=1)
        dist = DistributionAuthority(primary_channels=[channel])
        result = dist.check_cadence("LinkedIn", post_log)
        self.assertEqual(result["status"], "ANDON")

    def test_cadence_max_per_day_zero_no_warning(self):
        # max_per_day=0 means no cap → 3 posts today is fine
        channel = _make_channel(name="Newsletter", min_per_week=1, max_per_day=0)
        dist = DistributionAuthority(primary_channels=[channel])
        post_log = [_today(), _today(), _today()]
        result = dist.check_cadence("Newsletter", post_log)
        # min=1 and 3 posts in window → OK; no WARNING because max=0 (no cap)
        self.assertEqual(result["status"], "OK")

    def test_cadence_returns_cadence_metadata(self):
        post_log = [_days_ago(1)]
        result = self.distribution.check_cadence("LinkedIn", post_log)
        self.assertIn("min_per_week", result)
        self.assertIn("max_per_day", result)


class TestYAML(unittest.TestCase):
    def setUp(self):
        self.primary = _make_channel(name="LinkedIn", max_length=3000, required_elements=["hook", "CTA"])
        self.secondary = _make_channel(name="Substack", max_length=5000, required_elements=["intro"], is_primary=False, is_secondary=True)
        self.distribution = DistributionAuthority(
            primary_channels=[self.primary],
            secondary_channels=[self.secondary],
            donotbother_channels=["TikTok", "YouTube"],
        )

    def test_to_yaml_contains_primary_channel(self):
        yaml_str = to_yaml(self.distribution)
        self.assertIn("name: LinkedIn", yaml_str)
        self.assertIn("cadence_min_per_week: 1", yaml_str)

    def test_to_yaml_contains_donotbother(self):
        yaml_str = to_yaml(self.distribution)
        self.assertIn("TikTok", yaml_str)

    def test_from_yaml_roundtrip(self):
        yaml_str = to_yaml(self.distribution)
        restored = from_yaml(yaml_str)
        self.assertEqual(len(restored.primary_channels), 1)
        self.assertEqual(restored.primary_channels[0].name, "LinkedIn")
        self.assertEqual(restored.secondary_channels[0].name, "Substack")
        self.assertIn("TikTok", restored.donotbother_channels)

    def test_from_yaml_literal(self):
        yaml_str = """
version: '1.0'
date: '2026-06-27'
primary_channels:
- name: LinkedIn
  format_rules:
    max_length: 3000
    required_elements:
    - hook
    - CTA
    allowed_media_types: []
  cadence_min_per_week: 1
  cadence_max_per_day: 1
secondary_channels:
- name: X
  format_rules:
    max_length: 280
    required_elements:
    - hook
    allowed_media_types: []
  cadence_min_per_week: 3
  cadence_max_per_day: 2
donotbother_channels:
- TikTok
- YouTube
"""
        dist = from_yaml(yaml_str)
        self.assertEqual(len(dist.primary_channels), 1)
        self.assertEqual(dist.primary_channels[0].name, "LinkedIn")
        self.assertEqual(len(dist.secondary_channels), 1)
        self.assertEqual(dist.secondary_channels[0].name, "X")
        self.assertEqual(dist.donotbother_channels, ["TikTok", "YouTube"])


class TestMarkdown(unittest.TestCase):
    def setUp(self):
        primary = _make_channel(name="LinkedIn")
        secondary = _make_channel(name="Substack", is_primary=False, is_secondary=True)
        self.distribution = DistributionAuthority(
            primary_channels=[primary],
            secondary_channels=[secondary],
            donotbother_channels=["TikTok"],
        )

    def test_markdown_has_primary_section(self):
        md = self.distribution.to_markdown()
        self.assertIn("Primary Channels", md)
        self.assertIn("LinkedIn", md)

    def test_markdown_has_secondary_section(self):
        md = self.distribution.to_markdown()
        self.assertIn("Secondary Channels", md)
        self.assertIn("Substack", md)

    def test_markdown_has_donotbother_section(self):
        md = self.distribution.to_markdown()
        self.assertIn("Don't Bother", md)
        self.assertIn("TikTok", md)

    def test_markdown_has_version(self):
        md = self.distribution.to_markdown()
        self.assertIn("1.0", md)

    def test_markdown_no_secondary_section_when_empty(self):
        primary = _make_channel(name="LinkedIn")
        dist = DistributionAuthority(primary_channels=[primary])
        md = dist.to_markdown()
        self.assertNotIn("Secondary Channels", md)


if __name__ == "__main__":
    unittest.main()
