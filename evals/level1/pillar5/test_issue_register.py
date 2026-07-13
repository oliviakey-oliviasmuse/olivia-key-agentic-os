"""Tests for Pillar 5 Agent 1 — Issue Register Manager."""
import unittest
import os
import tempfile
from src.pillar5.issue_register import (
    Issue,
    VALID_CATEGORIES,
    VALID_TOLERANCES,
    generate_issue_id,
    format_issue_markdown,
)
from src.pillar5.issue_register_generator import create_issue, log_issue


# ── Helpers ────────────────────────────────────────────────────────────────

def make_issue(**overrides):
    defaults = dict(
        issue_description="Resource overrun on Client X",
        category="Cost",
        tolerance_dimension="cost",
        severity=4,
        proposed_resolution="Reallocate 10 hours from non-billable work",
    )
    defaults.update(overrides)
    return Issue(**defaults)


# ── Feature 1: Issue Creation ──────────────────────────────────────────────

class TestIssueCreation(unittest.TestCase):

    def test_happy_path_all_fields(self):
        issue = make_issue()
        self.assertEqual(issue.category, "Cost")
        self.assertEqual(issue.tolerance_dimension, "cost")
        self.assertEqual(issue.severity, 4)
        self.assertEqual(issue.escalation_level, "Critical")
        self.assertEqual(issue.status, "Open")
        self.assertIsNone(issue.check_and_on())

    def test_edge_case_min_severity(self):
        issue = make_issue(severity=1)
        self.assertEqual(issue.escalation_level, "Info")

    def test_edge_case_max_severity_with_resolution(self):
        issue = make_issue(severity=5, proposed_resolution="Emergency fix deployed")
        self.assertEqual(issue.escalation_level, "Critical")
        self.assertIsNone(issue.check_and_on())

    def test_optional_fields_default_correctly(self):
        issue = make_issue()
        self.assertEqual(issue.raised_by, "Olivia")
        self.assertIsNone(issue.closure_date)
        self.assertIsNone(issue.closure_notes)
        self.assertEqual(issue.status, "Open")

    def test_all_valid_categories_accepted(self):
        for cat in VALID_CATEGORIES:
            issue = make_issue(category=cat)
            self.assertEqual(issue.category, cat)

    def test_all_valid_tolerances_accepted(self):
        for tol in VALID_TOLERANCES:
            issue = make_issue(tolerance_dimension=tol)
            self.assertEqual(issue.tolerance_dimension, tol)


# ── Feature 2: Gate Enforcement ────────────────────────────────────────────

class TestGateEnforcement(unittest.TestCase):

    def test_g1_missing_description(self):
        with self.assertRaises(ValueError) as ctx:
            make_issue(issue_description="")
        self.assertIn("G1", str(ctx.exception))

    def test_g2_invalid_category(self):
        with self.assertRaises(ValueError) as ctx:
            make_issue(category="Invalid")
        self.assertIn("G2", str(ctx.exception))

    def test_g3_invalid_tolerance(self):
        with self.assertRaises(ValueError) as ctx:
            make_issue(tolerance_dimension="invalid")
        self.assertIn("G3", str(ctx.exception))

    def test_g4_severity_too_high(self):
        with self.assertRaises(ValueError) as ctx:
            make_issue(severity=6)
        self.assertIn("G4", str(ctx.exception))

    def test_g4_severity_too_low(self):
        with self.assertRaises(ValueError) as ctx:
            make_issue(severity=0)
        self.assertIn("G4", str(ctx.exception))

    def test_g4_severity_boundary_1_passes(self):
        issue = make_issue(severity=1)
        self.assertEqual(issue.severity, 1)

    def test_g4_severity_boundary_5_passes(self):
        issue = make_issue(severity=5)
        self.assertEqual(issue.severity, 5)


# ── Feature 3: Escalation Level Computation ────────────────────────────────

class TestEscalationLevel(unittest.TestCase):

    def test_severity_1_is_info(self):
        self.assertEqual(make_issue(severity=1).escalation_level, "Info")

    def test_severity_2_is_info(self):
        self.assertEqual(make_issue(severity=2).escalation_level, "Info")

    def test_severity_3_is_warning(self):
        self.assertEqual(make_issue(severity=3).escalation_level, "Warning")

    def test_severity_4_is_critical(self):
        self.assertEqual(make_issue(severity=4).escalation_level, "Critical")

    def test_severity_5_is_critical(self):
        self.assertEqual(make_issue(severity=5).escalation_level, "Critical")

    def test_escalation_level_not_overridden_if_provided(self):
        issue = make_issue(severity=1, escalation_level="Critical")
        self.assertEqual(issue.escalation_level, "Critical")


# ── Feature 4: ANDON Check (G5) ───────────────────────────────────────────

class TestANDONCheck(unittest.TestCase):

    def test_critical_with_no_resolution_triggers_andon(self):
        issue = make_issue(severity=5, proposed_resolution="")
        msg = issue.check_and_on()
        self.assertIsNotNone(msg)
        self.assertIn("ANDON", msg)

    def test_critical_with_resolution_no_andon(self):
        issue = make_issue(severity=5, proposed_resolution="Deploy hotfix immediately")
        self.assertIsNone(issue.check_and_on())

    def test_non_critical_with_no_resolution_no_andon(self):
        issue = make_issue(severity=2, proposed_resolution="")
        self.assertIsNone(issue.check_and_on())

    def test_warning_with_no_resolution_no_andon(self):
        issue = make_issue(severity=3, proposed_resolution="")
        self.assertIsNone(issue.check_and_on())


# ── Feature 5: Issue ID Generation ────────────────────────────────────────

class TestIssueIDGeneration(unittest.TestCase):

    def test_id_starts_with_iss_prefix(self):
        issue = make_issue(date_raised="2026-06-24")
        self.assertTrue(generate_issue_id(issue).startswith("ISS-20260624-"))

    def test_id_length_is_17(self):
        issue = make_issue(date_raised="2026-06-24")
        self.assertEqual(len(generate_issue_id(issue)), 17)

    def test_id_format_matches_expected_pattern(self):
        issue = make_issue(date_raised="2026-06-24")
        id_str = generate_issue_id(issue)
        parts = id_str.split('-')
        self.assertEqual(parts[0], "ISS")
        self.assertEqual(len(parts[1]), 8)
        self.assertEqual(len(parts[2]), 4)


# ── Feature 6: Markdown Format ────────────────────────────────────────────

class TestMarkdownFormat(unittest.TestCase):

    def test_normal_entry_contains_required_sections(self):
        issue = make_issue()
        md = format_issue_markdown(issue)
        self.assertIn("Issue Register Entry", md)
        self.assertIn("Date Raised", md)
        self.assertIn("Category", md)
        self.assertIn("Severity", md)
        self.assertIn("Escalation", md)
        self.assertIn("Proposed Resolution", md)
        self.assertIn("Status", md)

    def test_issue_description_appears_in_markdown(self):
        issue = make_issue(issue_description="Rework on output batch 14")
        md = format_issue_markdown(issue)
        self.assertIn("Rework on output batch 14", md)

    def test_severity_renders_as_x_over_5(self):
        issue = make_issue(severity=4)
        md = format_issue_markdown(issue)
        self.assertIn("4/5", md)

    def test_closure_fields_absent_when_not_set(self):
        issue = make_issue()
        md = format_issue_markdown(issue)
        self.assertNotIn("Closure Date", md)
        self.assertNotIn("Closure Notes", md)

    def test_closure_fields_render_when_provided(self):
        issue = make_issue(
            status="Closed",
            closure_date="2026-07-01",
            closure_notes="Root cause identified — process updated",
        )
        md = format_issue_markdown(issue)
        self.assertIn("Closure Date", md)
        self.assertIn("Closure Notes", md)
        self.assertIn("Root cause identified", md)

    def test_andon_markdown_blocks_entry_creation(self):
        issue = make_issue(severity=5, proposed_resolution="")
        md = format_issue_markdown(issue)
        self.assertIn("ANDON", md)
        self.assertNotIn("Issue Register Entry", md)

    def test_andon_markdown_contains_not_logged_notice(self):
        issue = make_issue(severity=5, proposed_resolution="")
        md = format_issue_markdown(issue)
        self.assertIn("not logged", md)


# ── Feature 7: Wrapper & Register Append ──────────────────────────────────

class TestWrapperAndRegister(unittest.TestCase):

    def test_create_issue_builds_correct_object(self):
        issue = create_issue(
            issue_description="Delay on milestone",
            category="Time",
            tolerance_dimension="time",
            severity=3,
            proposed_resolution="Compress remaining schedule",
        )
        self.assertEqual(issue.category, "Time")
        self.assertEqual(issue.escalation_level, "Warning")

    def test_log_issue_without_path_returns_markdown(self):
        issue = make_issue()
        md = log_issue(issue)
        self.assertIn("Issue Register Entry", md)

    def test_log_issue_appends_to_register_file(self):
        issue = make_issue()
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp_path = tmp.name
        log_issue(issue, register_path=tmp_path)
        with open(tmp_path, 'r') as f:
            content = f.read()
        self.assertIn("Issue Register Entry", content)
        os.remove(tmp_path)

    def test_log_issue_andon_returns_andon_markdown(self):
        issue = make_issue(severity=5, proposed_resolution="")
        md = log_issue(issue)
        self.assertIn("ANDON", md)

    def test_create_issue_default_raised_by(self):
        issue = create_issue("Test", "Risk", "risk", 2)
        self.assertEqual(issue.raised_by, "Olivia")

    def test_create_issue_none_resolution_becomes_empty_string(self):
        issue = create_issue("Test", "Risk", "risk", 2, proposed_resolution=None)
        self.assertEqual(issue.proposed_resolution, "")


if __name__ == "__main__":
    unittest.main()
