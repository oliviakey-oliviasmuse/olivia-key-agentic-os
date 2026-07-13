import unittest
from datetime import datetime, timedelta
from src.pillar0.drift_detector import (
    DriftRule,
    DriftBreach,
    DriftReport,
    check_rule,
    generate_drift_report,
    check_content_violations,
    check_proposal_below_floor,
    check_delivery_outside_icp,
    check_revenue_decline,
    METRIC_FUNCTIONS,
    VALID_ANDON_LEVELS,
)


def _now():
    return datetime.now().isoformat()


def _days_ago(n):
    return (datetime.now() - timedelta(days=n)).isoformat()


def _make_rule(**kwargs):
    defaults = dict(
        id="R1",
        description="Test rule",
        metric="content_violations",
        threshold=3.0,
        time_window_days=30,
        andon_level="CRITICAL",
    )
    defaults.update(kwargs)
    return DriftRule(**defaults)


class TestDriftRule(unittest.TestCase):
    def test_valid_rule(self):
        rule = _make_rule()
        self.assertEqual(rule.id, "R1")
        self.assertEqual(rule.threshold, 3.0)
        self.assertEqual(rule.escalation_path, "Owner")

    def test_g2_missing_id(self):
        with self.assertRaises(ValueError) as ctx:
            _make_rule(id="")
        self.assertIn("G2", str(ctx.exception))

    def test_g2_missing_description(self):
        with self.assertRaises(ValueError) as ctx:
            _make_rule(description="")
        self.assertIn("G2", str(ctx.exception))

    def test_g2_missing_metric(self):
        with self.assertRaises(ValueError) as ctx:
            _make_rule(metric="")
        self.assertIn("G2", str(ctx.exception))

    def test_g2_negative_threshold(self):
        with self.assertRaises(ValueError) as ctx:
            _make_rule(threshold=-1.0)
        self.assertIn("G2", str(ctx.exception))

    def test_g2_zero_time_window(self):
        with self.assertRaises(ValueError) as ctx:
            _make_rule(time_window_days=0)
        self.assertIn("G2", str(ctx.exception))

    def test_g2_negative_time_window(self):
        with self.assertRaises(ValueError) as ctx:
            _make_rule(time_window_days=-5)
        self.assertIn("G2", str(ctx.exception))

    def test_g2_invalid_andon_level(self):
        with self.assertRaises(ValueError) as ctx:
            _make_rule(andon_level="INVALID")
        self.assertIn("G2", str(ctx.exception))

    def test_all_andon_levels_valid(self):
        for level in VALID_ANDON_LEVELS:
            rule = _make_rule(id=f"R_{level}", andon_level=level)
            self.assertEqual(rule.andon_level, level)

    def test_zero_threshold_valid(self):
        # threshold=0 is allowed (fires on any event)
        rule = _make_rule(threshold=0.0)
        self.assertEqual(rule.threshold, 0.0)

    def test_custom_escalation_path(self):
        rule = _make_rule(escalation_path="COO")
        self.assertEqual(rule.escalation_path, "COO")


class TestMetrics(unittest.TestCase):
    # --- content_violations ---

    def test_content_violations_breach_at_threshold(self):
        events = [
            {"type": "content", "violation": True, "date": _now()},
            {"type": "content", "violation": True, "date": _now()},
        ]
        rule = _make_rule(metric="content_violations", threshold=2.0)
        result = check_rule(rule, {"feed": events})
        self.assertIsNotNone(result)
        self.assertEqual(result.actual_value, 2.0)

    def test_content_violations_no_breach_below_threshold(self):
        events = [
            {"type": "content", "violation": True, "date": _now()},
        ]
        rule = _make_rule(metric="content_violations", threshold=3.0)
        result = check_rule(rule, {"feed": events})
        self.assertIsNone(result)

    def test_content_violations_no_events(self):
        rule = _make_rule(metric="content_violations", threshold=1.0)
        result = check_rule(rule, {"feed": []})
        self.assertIsNone(result)

    def test_content_violations_non_violation_events_ignored(self):
        events = [
            {"type": "content", "violation": False, "date": _now()},
            {"type": "content", "violation": False, "date": _now()},
        ]
        rule = _make_rule(metric="content_violations", threshold=1.0)
        result = check_rule(rule, {"feed": events})
        self.assertIsNone(result)

    def test_content_old_events_filtered(self):
        # Event older than time window should not count
        events = [
            {"type": "content", "violation": True, "date": _days_ago(45)},
            {"type": "content", "violation": True, "date": _days_ago(35)},
        ]
        rule = _make_rule(metric="content_violations", threshold=1.0, time_window_days=30)
        result = check_rule(rule, {"feed": events})
        self.assertIsNone(result)

    # --- proposal_below_floor ---

    def test_proposal_below_floor_breach(self):
        events = [
            {"type": "proposal", "below_floor": True, "date": _now()},
            {"type": "proposal", "below_floor": False, "date": _now()},
        ]
        rule = _make_rule(metric="proposal_below_floor", threshold=1.0)
        result = check_rule(rule, {"feed": events})
        self.assertIsNotNone(result)
        self.assertEqual(result.actual_value, 1.0)

    def test_proposal_below_floor_no_breach(self):
        events = [
            {"type": "proposal", "below_floor": False, "date": _now()},
            {"type": "proposal", "below_floor": False, "date": _now()},
        ]
        rule = _make_rule(metric="proposal_below_floor", threshold=1.0)
        result = check_rule(rule, {"feed": events})
        self.assertIsNone(result)

    def test_proposal_below_floor_no_events(self):
        rule = _make_rule(metric="proposal_below_floor", threshold=1.0)
        result = check_rule(rule, {"feed": []})
        self.assertIsNone(result)

    # --- delivery_outside_icp ---

    def test_delivery_outside_icp_below_threshold(self):
        events = [
            {"type": "delivery", "outside_icp": True, "date": _now()},
            {"type": "delivery", "outside_icp": False, "date": _now()},
        ]
        rule = _make_rule(metric="delivery_outside_icp", threshold=2.0)
        result = check_rule(rule, {"feed": events})
        self.assertIsNone(result)

    def test_delivery_outside_icp_at_threshold(self):
        events = [
            {"type": "delivery", "outside_icp": True, "date": _now()},
            {"type": "delivery", "outside_icp": True, "date": _now()},
        ]
        rule = _make_rule(metric="delivery_outside_icp", threshold=2.0)
        result = check_rule(rule, {"feed": events})
        self.assertIsNotNone(result)
        self.assertEqual(result.actual_value, 2.0)

    def test_delivery_outside_icp_no_events(self):
        rule = _make_rule(metric="delivery_outside_icp", threshold=1.0)
        result = check_rule(rule, {"feed": []})
        self.assertIsNone(result)

    # --- revenue_decline ---

    def test_revenue_decline_breach(self):
        # Older event is outside 30-day window but must still be used for MoM
        events = [
            {"type": "revenue", "amount": 100000, "date": _days_ago(35)},
            {"type": "revenue", "amount": 80000, "date": _days_ago(5)},
        ]
        rule = _make_rule(metric="revenue_decline", threshold=20.0, time_window_days=30, andon_level="WARNING")
        result = check_rule(rule, {"feed": events})
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result.actual_value, 20.0)

    def test_revenue_decline_no_breach(self):
        events = [
            {"type": "revenue", "amount": 100000, "date": _days_ago(35)},
            {"type": "revenue", "amount": 95000, "date": _days_ago(5)},
        ]
        rule = _make_rule(metric="revenue_decline", threshold=20.0, time_window_days=30, andon_level="WARNING")
        result = check_rule(rule, {"feed": events})
        self.assertIsNone(result)

    def test_revenue_decline_no_data(self):
        rule = _make_rule(metric="revenue_decline", threshold=20.0)
        result = check_rule(rule, {"feed": []})
        self.assertIsNone(result)

    def test_revenue_decline_only_one_entry(self):
        events = [{"type": "revenue", "amount": 80000, "date": _days_ago(5)}]
        rule = _make_rule(metric="revenue_decline", threshold=1.0)
        result = check_rule(rule, {"feed": events})
        self.assertIsNone(result)

    def test_revenue_decline_prev_zero_no_crash(self):
        events = [
            {"type": "revenue", "amount": 0, "date": _days_ago(35)},
            {"type": "revenue", "amount": 80000, "date": _days_ago(5)},
        ]
        rule = _make_rule(metric="revenue_decline", threshold=1.0)
        result = check_rule(rule, {"feed": events})
        self.assertIsNone(result)

    # --- unknown metric ---

    def test_unknown_metric_returns_none(self):
        rule = _make_rule(metric="undefined_metric")
        result = check_rule(rule, {"feed": [{"type": "content", "violation": True, "date": _now()}]})
        self.assertIsNone(result)

    # --- multi-feed ---

    def test_events_from_multiple_feeds_combined(self):
        feed1 = [{"type": "content", "violation": True, "date": _now()}]
        feed2 = [{"type": "content", "violation": True, "date": _now()}]
        rule = _make_rule(metric="content_violations", threshold=2.0)
        result = check_rule(rule, {"p2": feed1, "p3": feed2})
        self.assertIsNotNone(result)
        self.assertEqual(result.actual_value, 2.0)


class TestDriftReport(unittest.TestCase):
    def _make_breach(self, rule_id="R1", andon_level="CRITICAL"):
        return DriftBreach(
            rule_id=rule_id,
            andon_level=andon_level,
            actual_value=3.0,
            threshold=2.0,
            details="Test breach",
            escalation_path="Owner",
        )

    def test_generate_report_no_breaches(self):
        rule = _make_rule(threshold=10.0)
        events = [{"type": "content", "violation": False, "date": _now()}]
        report = generate_drift_report([rule], {"feed": events})
        self.assertEqual(len(report.breaches), 0)
        self.assertIn("No Breaches", report.to_markdown())

    def test_generate_report_with_breach(self):
        rule = _make_rule(threshold=1.0)
        events = [
            {"type": "content", "violation": True, "date": _now()},
            {"type": "content", "violation": True, "date": _now()},
        ]
        report = generate_drift_report([rule], {"feed": events})
        self.assertEqual(len(report.breaches), 1)
        md = report.to_markdown()
        self.assertIn("Breaches", md)
        self.assertNotIn("No Breaches", md)

    def test_g1_empty_rules(self):
        with self.assertRaises(ValueError) as ctx:
            generate_drift_report([], {})
        self.assertIn("G1", str(ctx.exception))

    def test_multiple_rules_all_pass(self):
        rules = [
            _make_rule(id="R1", threshold=10.0),
            _make_rule(id="R2", metric="proposal_below_floor", threshold=5.0),
        ]
        report = generate_drift_report(rules, {"feed": []})
        self.assertEqual(report.rules_checked, 2)
        self.assertEqual(len(report.breaches), 0)

    def test_multiple_rules_partial_breach(self):
        rules = [
            _make_rule(id="R1", metric="content_violations", threshold=1.0),
            _make_rule(id="R2", metric="proposal_below_floor", threshold=5.0),
        ]
        events = [{"type": "content", "violation": True, "date": _now()}]
        report = generate_drift_report(rules, {"feed": events})
        self.assertEqual(len(report.breaches), 1)
        self.assertEqual(report.breaches[0].rule_id, "R1")

    def test_markdown_summary_rules_checked(self):
        rules = [_make_rule(id="R1"), _make_rule(id="R2", metric="proposal_below_floor")]
        report = generate_drift_report(rules, {"feed": []})
        md = report.to_markdown()
        self.assertIn("Rules checked: 2", md)

    def test_markdown_summary_breach_count(self):
        rule = _make_rule(threshold=1.0)
        events = [
            {"type": "content", "violation": True, "date": _now()},
            {"type": "content", "violation": True, "date": _now()},
        ]
        report = generate_drift_report([rule], {"feed": events})
        md = report.to_markdown()
        self.assertIn("Breaches: 1", md)

    def test_markdown_andon_count_critical_only(self):
        breach_critical = self._make_breach(rule_id="R1", andon_level="CRITICAL")
        breach_warning = self._make_breach(rule_id="R2", andon_level="WARNING")
        report = DriftReport(date="2026-06-27", rules_checked=2, breaches=[breach_critical, breach_warning])
        md = report.to_markdown()
        self.assertIn("ANDONs: 1", md)

    def test_markdown_has_rule_id_in_table(self):
        rule = _make_rule(id="DRIFT-001", threshold=1.0)
        events = [{"type": "content", "violation": True, "date": _now()}]
        report = generate_drift_report([rule], {"feed": events})
        md = report.to_markdown()
        self.assertIn("DRIFT-001", md)

    def test_markdown_has_escalation_path(self):
        rule = _make_rule(threshold=1.0, escalation_path="COO")
        events = [{"type": "content", "violation": True, "date": _now()}]
        report = generate_drift_report([rule], {"feed": events})
        md = report.to_markdown()
        self.assertIn("COO", md)

    def test_breach_andon_level_in_table(self):
        rule = _make_rule(threshold=1.0, andon_level="WARNING")
        events = [{"type": "content", "violation": True, "date": _now()}]
        report = generate_drift_report([rule], {"feed": events})
        md = report.to_markdown()
        self.assertIn("WARNING", md)

    def test_report_date_in_header(self):
        rule = _make_rule()
        report = generate_drift_report([rule], {"feed": []}, date="2026-06-27T00:00:00")
        md = report.to_markdown()
        self.assertIn("2026-06-27", md)

    def test_empty_data_feed_no_crash(self):
        rule = _make_rule(threshold=1.0)
        report = generate_drift_report([rule], {})
        self.assertEqual(len(report.breaches), 0)


if __name__ == "__main__":
    unittest.main()
