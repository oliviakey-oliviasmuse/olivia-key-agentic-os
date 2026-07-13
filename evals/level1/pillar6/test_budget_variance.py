import unittest
import os
import tempfile
from src.pillar6.budget_variance import (
    BudgetLine,
    compute_summary,
    generate_variance_report,
    validate_inputs,
)
from src.pillar6.budget_variance_generator import log_escalations_to_issue_register


class TestBudgetLineVariance(unittest.TestCase):
    def test_overspend_variance(self):
        line = BudgetLine(name='Test', budgeted_amount=100, actual_amount=115)
        self.assertAlmostEqual(line.variance(), 15.0)

    def test_underspend_variance(self):
        line = BudgetLine(name='Test', budgeted_amount=100, actual_amount=90)
        self.assertAlmostEqual(line.variance(), -10.0)

    def test_zero_variance(self):
        line = BudgetLine(name='Test', budgeted_amount=100, actual_amount=100)
        self.assertEqual(line.variance(), 0.0)

    def test_zero_budget_returns_zero(self):
        # G3 boundary: budgeted_amount == 0 returns 0.0 rather than ZeroDivisionError
        line = BudgetLine(name='Test', budgeted_amount=0, actual_amount=50)
        self.assertEqual(line.variance(), 0.0)


class TestBudgetLineStatus(unittest.TestCase):
    def test_status_ok(self):
        line = BudgetLine(name='Test', budgeted_amount=100, actual_amount=102)
        self.assertEqual(line.status(), 'OK')

    def test_status_ok_boundary_at_5pct(self):
        # exactly 5% → OK (≤ warning_threshold)
        line = BudgetLine(name='Test', budgeted_amount=100, actual_amount=105)
        self.assertEqual(line.status(), 'OK')

    def test_status_warning(self):
        line = BudgetLine(name='Test', budgeted_amount=100, actual_amount=108)
        self.assertEqual(line.status(), 'WARNING')

    def test_status_warning_boundary_at_10pct(self):
        # exactly 10% → WARNING (≤ escalate_threshold, spec: WARNING if 5% < |var| ≤ 10%)
        line = BudgetLine(name='Test', budgeted_amount=100, actual_amount=110)
        self.assertEqual(line.status(), 'WARNING')

    def test_status_escalate(self):
        line = BudgetLine(name='Test', budgeted_amount=100, actual_amount=115)
        self.assertEqual(line.status(), 'ESCALATE')

    def test_status_escalate_boundary_just_over_10pct(self):
        # 10.1% → ESCALATE (> escalate_threshold)
        line = BudgetLine(name='Test', budgeted_amount=1000, actual_amount=1101)
        self.assertEqual(line.status(), 'ESCALATE')

    def test_underspend_status_warning(self):
        # underspend is equally flaggable — -8% → WARNING
        line = BudgetLine(name='Test', budgeted_amount=100, actual_amount=92)
        self.assertEqual(line.status(), 'WARNING')

    def test_underspend_status_escalate(self):
        # -15% underspend → ESCALATE (idle capacity is waste)
        line = BudgetLine(name='Test', budgeted_amount=100, actual_amount=85)
        self.assertEqual(line.status(), 'ESCALATE')


class TestGateEnforcement(unittest.TestCase):
    def test_g1_missing_period(self):
        with self.assertRaises(ValueError) as ctx:
            validate_inputs('', [BudgetLine('A', 100, 100)])
        self.assertIn('G1', str(ctx.exception))

    def test_g2_empty_lines(self):
        with self.assertRaises(ValueError) as ctx:
            validate_inputs('Q3 2026', [])
        self.assertIn('G2', str(ctx.exception))

    def test_g1_and_g2_raised_from_report(self):
        with self.assertRaises(ValueError):
            generate_variance_report([], '')

    def test_g3_zero_budget_line_skipped_in_report(self):
        lines = [
            BudgetLine(name='Valid', budgeted_amount=100, actual_amount=100),
            BudgetLine(name='ZeroBudget', budgeted_amount=0, actual_amount=50),
        ]
        report = generate_variance_report(lines, 'Q3 2026')
        self.assertIn('G3 WARNING', report)
        self.assertIn('ZeroBudget', report)
        # ZeroBudget must not appear in the table (skipped)
        self.assertNotIn('| ZeroBudget |', report)

    def test_g4_negative_actual_flagged_in_report(self):
        lines = [BudgetLine(name='NegActual', budgeted_amount=1000, actual_amount=-100)]
        report = generate_variance_report(lines, 'Q3 2026')
        self.assertIn('G4 WARNING', report)
        self.assertIn('NegActual', report)


class TestComputeSummary(unittest.TestCase):
    def test_balanced_budget_overall_variance_zero(self):
        # A: -10% (WARNING), B: +5% (OK) → totals balance to 0% overall
        lines = [
            BudgetLine(name='A', budgeted_amount=100, actual_amount=90),
            BudgetLine(name='B', budgeted_amount=200, actual_amount=210),
        ]
        summary = compute_summary(lines)
        self.assertEqual(summary['total_budget'], 300)
        self.assertEqual(summary['total_actual'], 300)
        self.assertAlmostEqual(summary['overall_variance'], 0.0)
        # A at -10% is WARNING (≤10%), B at +5% is OK
        self.assertEqual(summary['ok_count'], 1)
        self.assertEqual(summary['warning_count'], 1)
        self.assertEqual(summary['escalate_count'], 0)

    def test_summary_with_escalation(self):
        lines = [
            BudgetLine(name='A', budgeted_amount=100, actual_amount=90),   # -10% WARNING
            BudgetLine(name='B', budgeted_amount=200, actual_amount=250),  # +25% ESCALATE
        ]
        summary = compute_summary(lines)
        self.assertEqual(summary['ok_count'], 0)
        self.assertEqual(summary['warning_count'], 1)
        self.assertEqual(summary['escalate_count'], 1)

    def test_all_ok(self):
        lines = [
            BudgetLine(name='A', budgeted_amount=100, actual_amount=103),  # +3% OK
            BudgetLine(name='B', budgeted_amount=200, actual_amount=198),  # -1% OK
        ]
        summary = compute_summary(lines)
        self.assertEqual(summary['ok_count'], 2)
        self.assertEqual(summary['warning_count'], 0)
        self.assertEqual(summary['escalate_count'], 0)

    def test_empty_lines_overall_variance_zero(self):
        summary = compute_summary([])
        self.assertEqual(summary['total_budget'], 0.0)
        self.assertEqual(summary['overall_variance'], 0.0)


class TestReportGeneration(unittest.TestCase):
    def test_report_period_in_header(self):
        lines = [BudgetLine(name='Marketing', budgeted_amount=1000, actual_amount=950)]
        report = generate_variance_report(lines, 'Q3 2026')
        self.assertIn('Q3 2026', report)

    def test_report_contains_line_items(self):
        lines = [
            BudgetLine(name='Marketing', budgeted_amount=1000, actual_amount=950),  # -5.0% OK
            BudgetLine(name='Ops', budgeted_amount=2000, actual_amount=2300),       # +15.0% ESCALATE
        ]
        report = generate_variance_report(lines, 'Q3 2026')
        self.assertIn('Marketing', report)
        self.assertIn('-5.0%', report)
        self.assertIn('Ops', report)
        self.assertIn('+15.0%', report)
        self.assertIn('Summary', report)

    def test_report_escalation_section_present(self):
        lines = [
            BudgetLine(name='Ops', budgeted_amount=2000, actual_amount=2300),  # +15% ESCALATE
        ]
        report = generate_variance_report(lines, 'Q3 2026')
        self.assertIn('ESCALATE', report)
        self.assertIn('Escalations', report)
        self.assertIn('Issue Register', report)

    def test_report_no_escalation_section_when_all_ok(self):
        lines = [BudgetLine(name='A', budgeted_amount=100, actual_amount=102)]
        report = generate_variance_report(lines, 'Q3 2026')
        self.assertNotIn('Escalations', report)

    def test_report_warning_line_not_in_escalations(self):
        # +8% is WARNING not ESCALATE — must not appear in escalation section
        lines = [BudgetLine(name='Wages', budgeted_amount=1000, actual_amount=1080)]
        report = generate_variance_report(lines, 'Q3 2026')
        self.assertIn('WARNING', report)
        self.assertNotIn('Escalations', report)

    def test_report_underspend_escalates(self):
        # -15% underspend → ESCALATE (idle capacity is waste)
        lines = [BudgetLine(name='Tools', budgeted_amount=1000, actual_amount=850)]
        report = generate_variance_report(lines, 'Q3 2026')
        self.assertIn('ESCALATE', report)
        self.assertIn('-15.0%', report)


class TestEscalationLogging(unittest.TestCase):
    def test_no_escalations_returns_message(self):
        lines = [BudgetLine(name='A', budgeted_amount=100, actual_amount=103)]
        result = log_escalations_to_issue_register(lines)
        self.assertEqual(result, "No escalations to log.")

    def test_escalation_returned_as_string(self):
        lines = [BudgetLine(name='Ops', budgeted_amount=2000, actual_amount=2300)]
        result = log_escalations_to_issue_register(lines)
        self.assertIn('Ops', result)
        self.assertIn('+15.0%', result)

    def test_escalation_appended_to_file(self):
        lines = [BudgetLine(name='Ops', budgeted_amount=2000, actual_amount=2300)]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            path = f.name
        try:
            log_escalations_to_issue_register(lines, issue_register_path=path)
            with open(path, encoding='utf-8') as f:
                content = f.read()
            self.assertIn('Ops', content)
            self.assertIn('Budget Variance Escalations', content)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
