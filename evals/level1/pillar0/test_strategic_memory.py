import unittest
from datetime import datetime, timedelta
from src.pillar0.strategic_memory import (
    StrategicDecision,
    StrategicMemory,
    log_decision,
    to_yaml,
    from_yaml,
    VALID_DECISION_TYPES,
)


def _days_ago(n):
    return (datetime.now() - timedelta(days=n)).strftime("%Y-%m-%d")


def _today():
    return datetime.now().strftime("%Y-%m-%d")


def _make_memory():
    return StrategicMemory(
        decisions=[],
        current_quarter="Q2 2026",
        quarter_start="2026-04-01",
        quarter_end="2026-06-30",
    )


class TestStrategicDecision(unittest.TestCase):
    def test_valid_decision(self):
        decision = StrategicDecision(
            decision_id="DEC-001",
            decision_type="ICP_Change",
            description="Expanded ICP to logistics",
            rationale="3 qualified leads in Q1",
            date="2026-03-31",
            enacted=True,
        )
        self.assertEqual(decision.decision_id, "DEC-001")

    def test_g1_missing_id(self):
        with self.assertRaises(ValueError) as ctx:
            StrategicDecision(decision_id="", decision_type="ICP_Change", description="Test", rationale="Test", date="2026-03-31")
        self.assertIn("G1", str(ctx.exception))

    def test_g2_invalid_type(self):
        with self.assertRaises(ValueError) as ctx:
            StrategicDecision(decision_id="DEC-001", decision_type="Invalid", description="Test", rationale="Test", date="2026-03-31")
        self.assertIn("G2", str(ctx.exception))

    def test_g3_missing_description(self):
        with self.assertRaises(ValueError) as ctx:
            StrategicDecision(decision_id="DEC-001", decision_type="ICP_Change", description="", rationale="Test", date="2026-03-31")
        self.assertIn("G3", str(ctx.exception))

    def test_g4_missing_rationale(self):
        with self.assertRaises(ValueError) as ctx:
            StrategicDecision(decision_id="DEC-001", decision_type="ICP_Change", description="Test", rationale="", date="2026-03-31")
        self.assertIn("G4", str(ctx.exception))

    def test_g5_invalid_date(self):
        with self.assertRaises(ValueError) as ctx:
            StrategicDecision(decision_id="DEC-001", decision_type="ICP_Change", description="Test", rationale="Test", date="2026-99-99")
        self.assertIn("G5", str(ctx.exception))

    def test_g5_invalid_review_date(self):
        with self.assertRaises(ValueError) as ctx:
            StrategicDecision(
                decision_id="DEC-001", decision_type="ICP_Change", description="Test", rationale="Test",
                date="2026-03-31", review_required=True, review_date="not-a-date",
            )
        self.assertIn("G5", str(ctx.exception))

    def test_all_valid_decision_types(self):
        for dt in VALID_DECISION_TYPES:
            d = StrategicDecision(decision_id=f"DEC-{dt}", decision_type=dt, description="Test", rationale="Test", date="2026-06-27")
            self.assertEqual(d.decision_type, dt)

    def test_enacted_defaults_true(self):
        d = StrategicDecision(decision_id="DEC-001", decision_type="Strategy_Shift", description="Test", rationale="Test", date="2026-06-27")
        self.assertTrue(d.enacted)

    def test_review_required_with_review_date(self):
        d = StrategicDecision(
            decision_id="DEC-001", decision_type="ICP_Change", description="Test", rationale="Test",
            date="2026-03-31", review_required=True, review_date="2026-09-30",
        )
        self.assertTrue(d.review_required)
        self.assertEqual(d.review_date, "2026-09-30")

    def test_enacted_false_stored(self):
        d = StrategicDecision(decision_id="DEC-001", decision_type="ICP_Change", description="Test", rationale="Test", date="2026-06-27", enacted=False)
        self.assertFalse(d.enacted)


class TestStrategicMemory(unittest.TestCase):
    def setUp(self):
        self.memory = _make_memory()

    def test_log_decision_appends(self):
        log_decision(self.memory, "DEC-001", "ICP_Change", "Expanded ICP", "Qualified leads", "2026-03-31")
        self.assertEqual(len(self.memory.decisions), 1)
        self.assertEqual(self.memory.decisions[0].decision_id, "DEC-001")

    def test_log_decision_multiple(self):
        log_decision(self.memory, "DEC-001", "ICP_Change", "Test", "Test", "2026-04-01")
        log_decision(self.memory, "DEC-002", "Pricing_Change", "Test", "Test", "2026-05-01")
        log_decision(self.memory, "DEC-003", "Strategy_Shift", "Test", "Test", "2026-06-01")
        self.assertEqual(len(self.memory.decisions), 3)

    def test_get_decisions_returns_all(self):
        log_decision(self.memory, "DEC-001", "ICP_Change", "Test", "Test", "2026-04-01")
        log_decision(self.memory, "DEC-002", "Pricing_Change", "Test", "Test", "2026-05-01")
        self.assertEqual(len(self.memory.get_decisions()), 2)

    def test_get_decisions_by_type_icp(self):
        log_decision(self.memory, "DEC-001", "ICP_Change", "Test", "Test", "2026-03-31")
        log_decision(self.memory, "DEC-002", "Pricing_Change", "Test", "Test", "2026-03-31")
        icp = self.memory.get_decisions_by_type("ICP_Change")
        self.assertEqual(len(icp), 1)
        self.assertEqual(icp[0].decision_id, "DEC-001")

    def test_get_decisions_by_type_empty_when_none(self):
        log_decision(self.memory, "DEC-001", "ICP_Change", "Test", "Test", "2026-03-31")
        shifts = self.memory.get_decisions_by_type("Strategy_Shift")
        self.assertEqual(len(shifts), 0)

    def test_get_recent_decisions_filters_old(self):
        log_decision(self.memory, "DEC-001", "ICP_Change", "Old", "Old", _days_ago(100))
        log_decision(self.memory, "DEC-002", "Pricing_Change", "New", "New", _days_ago(10))
        recent = self.memory.get_recent_decisions(30)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0].decision_id, "DEC-002")

    def test_get_recent_decisions_includes_boundary(self):
        log_decision(self.memory, "DEC-001", "ICP_Change", "Test", "Test", _days_ago(30))
        recent = self.memory.get_recent_decisions(30)
        # Boundary: exactly 30 days ago should be included (>= cutoff)
        self.assertEqual(len(recent), 1)

    def test_get_recent_decisions_empty(self):
        recent = self.memory.get_recent_decisions(30)
        self.assertEqual(len(recent), 0)

    def test_get_strategic_context_counts(self):
        log_decision(self.memory, "DEC-001", "ICP_Change", "Test", "Test", _days_ago(10))
        log_decision(self.memory, "DEC-002", "Pricing_Change", "Test", "Test", _days_ago(5))
        log_decision(self.memory, "DEC-003", "Offer_Change", "Test", "Test", _days_ago(2))
        context = self.memory.get_strategic_context()
        self.assertEqual(context["recent_decisions_count"], 3)
        self.assertEqual(context["icp_changes"], 1)
        self.assertEqual(context["pricing_changes"], 1)
        self.assertEqual(context["offer_changes"], 1)

    def test_get_strategic_context_empty(self):
        context = self.memory.get_strategic_context()
        self.assertEqual(context["recent_decisions_count"], 0)
        self.assertEqual(context["quarter"], "Q2 2026")

    def test_get_strategic_context_all_types(self):
        for i, dt in enumerate(VALID_DECISION_TYPES):
            log_decision(self.memory, f"DEC-{i:03d}", dt, "Test", "Test", _days_ago(i + 1))
        context = self.memory.get_strategic_context()
        self.assertEqual(context["recent_decisions_count"], len(VALID_DECISION_TYPES))
        self.assertEqual(context["icp_changes"], 1)
        self.assertEqual(context["strategy_shifts"], 1)

    def test_get_decisions_requiring_review(self):
        log_decision(self.memory, "DEC-001", "ICP_Change", "Test", "Test", "2026-03-31", review_required=True, review_date="2026-09-30")
        log_decision(self.memory, "DEC-002", "Pricing_Change", "Test", "Test", "2026-04-01")
        pending = self.memory.get_decisions_requiring_review()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].decision_id, "DEC-001")


class TestMarkdown(unittest.TestCase):
    def setUp(self):
        self.memory = _make_memory()

    def test_to_markdown_contains_quarter(self):
        md = self.memory.to_markdown()
        self.assertIn("Q2 2026", md)

    def test_to_markdown_no_recent_decisions(self):
        md = self.memory.to_markdown()
        self.assertIn("No recent decisions", md)

    def test_to_markdown_with_decision(self):
        log_decision(self.memory, "DEC-001", "ICP_Change", "Expanded ICP", "Qualified leads", "2026-06-01")
        md = self.memory.to_markdown()
        self.assertIn("DEC-001", md)
        self.assertIn("ICP_Change", md)

    def test_to_markdown_enacted_no(self):
        log_decision(self.memory, "DEC-001", "Strategy_Shift", "Test", "Test", _days_ago(5), enacted=False)
        md = self.memory.to_markdown()
        self.assertIn("No", md)

    def test_to_markdown_strategic_context_section(self):
        md = self.memory.to_markdown()
        self.assertIn("Strategic Context", md)

    def test_quarterly_snapshot_no_decisions(self):
        snap = self.memory.generate_quarterly_snapshot()
        self.assertIn("Q2 2026", snap)
        self.assertIn("No decisions logged this quarter", snap)

    def test_quarterly_snapshot_with_quarter_decision(self):
        log_decision(self.memory, "DEC-001", "Pricing_Change", "Raised floor", "Market data", "2026-05-01")
        snap = self.memory.generate_quarterly_snapshot()
        self.assertIn("DEC-001", snap)
        self.assertIn("Pricing_Change", snap)

    def test_quarterly_snapshot_excludes_out_of_quarter(self):
        # Decision before the quarter
        log_decision(self.memory, "DEC-001", "ICP_Change", "Old decision", "Old reason", "2026-03-15")
        snap = self.memory.generate_quarterly_snapshot()
        self.assertNotIn("DEC-001", snap)

    def test_quarterly_snapshot_shows_pending_reviews(self):
        log_decision(
            self.memory, "DEC-001", "ICP_Change", "Test", "Test", "2026-05-01",
            review_required=True, review_date="2026-09-30",
        )
        snap = self.memory.generate_quarterly_snapshot()
        self.assertIn("Pending Reviews", snap)
        self.assertIn("2026-09-30", snap)


class TestYAML(unittest.TestCase):
    def test_to_yaml_has_decision(self):
        memory = _make_memory()
        log_decision(memory, "DEC-001", "ICP_Change", "Test", "Test", "2026-03-31")
        yaml_str = to_yaml(memory)
        self.assertIn("DEC-001", yaml_str)
        self.assertIn("Q2 2026", yaml_str)

    def test_to_yaml_has_quarter_fields(self):
        memory = _make_memory()
        yaml_str = to_yaml(memory)
        self.assertIn("quarter_start:", yaml_str)
        self.assertIn("2026-04-01", yaml_str)
        self.assertIn("quarter_end:", yaml_str)
        self.assertIn("2026-06-30", yaml_str)

    def test_from_yaml_literal(self):
        yaml_str = """
version: '1.0'
last_updated: '2026-06-27T00:00:00'
current_quarter: Q2 2026
quarter_start: '2026-04-01'
quarter_end: '2026-06-30'
decisions:
- decision_id: DEC-001
  decision_type: ICP_Change
  description: Expanded ICP
  rationale: Qualified leads
  date: '2026-03-31'
  enacted: true
  review_required: false
  review_date: null
"""
        memory = from_yaml(yaml_str)
        self.assertEqual(len(memory.decisions), 1)
        self.assertEqual(memory.decisions[0].decision_id, "DEC-001")
        self.assertEqual(memory.current_quarter, "Q2 2026")

    def test_from_yaml_roundtrip(self):
        memory = _make_memory()
        log_decision(memory, "DEC-001", "ICP_Change", "Test decision", "Solid rationale", "2026-05-15", review_required=True, review_date="2026-09-30")
        log_decision(memory, "DEC-002", "Pricing_Change", "Raised floor", "Market data", "2026-06-01", enacted=False)
        yaml_str = to_yaml(memory)
        restored = from_yaml(yaml_str)
        self.assertEqual(len(restored.decisions), 2)
        self.assertEqual(restored.decisions[0].decision_id, "DEC-001")
        self.assertTrue(restored.decisions[0].review_required)
        self.assertEqual(restored.decisions[0].review_date, "2026-09-30")
        self.assertFalse(restored.decisions[1].enacted)
        self.assertEqual(restored.current_quarter, "Q2 2026")

    def test_from_yaml_version_stored_as_string(self):
        yaml_str = """
version: 1.0
last_updated: '2026-06-27'
current_quarter: Q2 2026
quarter_start: '2026-04-01'
quarter_end: '2026-06-30'
decisions: []
"""
        memory = from_yaml(yaml_str)
        self.assertIsInstance(memory.version, str)


if __name__ == "__main__":
    unittest.main()
