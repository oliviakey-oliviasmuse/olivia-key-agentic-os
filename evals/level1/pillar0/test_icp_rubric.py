import unittest
from src.pillar0.icp_rubric import (
    ICPScore,
    BusinessCaseFilter,
    THRESHOLD_PROCEED,
    THRESHOLD_DEFER,
    compute_rubric_summary,
    generate_icp_report,
)
from src.pillar0.icp_rubric_generator import score_prospect, apply_bc_filter, get_icp_report


class TestICPScoreGates(unittest.TestCase):

    def test_valid_score(self):
        s = ICPScore(
            prospect_name='James Okafor',
            company_size=5,
            sector_fit=5,
            role_title=5,
            pain_indicators=4,
            budget_authority=4,
            date='2026-06-01',
        )
        self.assertEqual(s.total, 23)
        self.assertEqual(s.verdict, 'PROCEED')

    def test_g1_missing_name(self):
        with self.assertRaises(ValueError) as ctx:
            ICPScore('', 3, 3, 3, 3, 3)
        self.assertIn('G1', str(ctx.exception))

    def test_g2_score_zero_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            ICPScore('James', 0, 3, 3, 3, 3)
        self.assertIn('G2', str(ctx.exception))

    def test_g2_score_six_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            ICPScore('James', 6, 3, 3, 3, 3)
        self.assertIn('G2', str(ctx.exception))

    def test_g2_all_criteria_validated(self):
        for criterion, kwargs in [
            ('sector_fit',       dict(company_size=3, sector_fit=0,  role_title=3, pain_indicators=3, budget_authority=3)),
            ('role_title',       dict(company_size=3, sector_fit=3,  role_title=0, pain_indicators=3, budget_authority=3)),
            ('pain_indicators',  dict(company_size=3, sector_fit=3,  role_title=3, pain_indicators=0, budget_authority=3)),
            ('budget_authority', dict(company_size=3, sector_fit=3,  role_title=3, pain_indicators=3, budget_authority=0)),
        ]:
            with self.subTest(criterion=criterion):
                with self.assertRaises(ValueError) as ctx:
                    ICPScore('James', **kwargs)
                self.assertIn('G2', str(ctx.exception))

    def test_g3_invalid_date(self):
        with self.assertRaises(ValueError) as ctx:
            ICPScore('James', 3, 3, 3, 3, 3, date='not-a-date')
        self.assertIn('G3', str(ctx.exception))


class TestICPScoreVerdicts(unittest.TestCase):

    def test_proceed_at_threshold(self):
        s = ICPScore('x', 4, 4, 4, 3, 3)  # total = 18
        self.assertEqual(s.total, 18)
        self.assertEqual(s.verdict, 'PROCEED')

    def test_proceed_above_threshold(self):
        s = ICPScore('x', 5, 5, 5, 5, 5)  # total = 25
        self.assertEqual(s.verdict, 'PROCEED')

    def test_defer_just_below_proceed(self):
        s = ICPScore('x', 4, 4, 3, 3, 3)  # total = 17
        self.assertEqual(s.total, 17)
        self.assertEqual(s.verdict, 'DEFER')

    def test_defer_at_lower_threshold(self):
        s = ICPScore('x', 3, 3, 2, 2, 2)  # total = 12
        self.assertEqual(s.total, 12)
        self.assertEqual(s.verdict, 'DEFER')

    def test_reject_just_below_defer(self):
        s = ICPScore('x', 3, 2, 2, 2, 2)  # total = 11
        self.assertEqual(s.total, 11)
        self.assertEqual(s.verdict, 'REJECT')

    def test_reject_minimum_score(self):
        s = ICPScore('x', 1, 1, 1, 1, 1)  # total = 5
        self.assertEqual(s.verdict, 'REJECT')

    def test_total_is_sum_of_criteria(self):
        s = ICPScore('x', 2, 3, 4, 5, 1)
        self.assertEqual(s.total, 15)


class TestBusinessCaseFilter(unittest.TestCase):

    def test_all_pass(self):
        bc = BusinessCaseFilter('James', viable=True, desirable=True, achievable=True)
        self.assertTrue(bc.passes)
        self.assertEqual(bc.verdict, 'PASS')
        self.assertEqual(bc.failed_dimensions(), [])

    def test_viable_fails(self):
        bc = BusinessCaseFilter('James', viable=False, desirable=True, achievable=True)
        self.assertFalse(bc.passes)
        self.assertIn('viable', bc.failed_dimensions())

    def test_desirable_fails(self):
        bc = BusinessCaseFilter('James', viable=True, desirable=False, achievable=True)
        self.assertFalse(bc.passes)
        self.assertIn('desirable', bc.failed_dimensions())

    def test_achievable_fails(self):
        bc = BusinessCaseFilter('James', viable=True, desirable=True, achievable=False)
        self.assertFalse(bc.passes)
        self.assertIn('achievable', bc.failed_dimensions())

    def test_all_fail(self):
        bc = BusinessCaseFilter('James', viable=False, desirable=False, achievable=False)
        self.assertFalse(bc.passes)
        self.assertEqual(len(bc.failed_dimensions()), 3)

    def test_g1_missing_name(self):
        with self.assertRaises(ValueError) as ctx:
            BusinessCaseFilter('', viable=True, desirable=True, achievable=True)
        self.assertIn('G1', str(ctx.exception))

    def test_verdict_fail_string(self):
        bc = BusinessCaseFilter('James', viable=False, desirable=True, achievable=True)
        self.assertEqual(bc.verdict, 'FAIL')


class TestRubricSummary(unittest.TestCase):

    def test_summary_mixed(self):
        scores = [
            ICPScore('A', 5, 5, 5, 4, 4),   # 23 → PROCEED
            ICPScore('B', 3, 3, 3, 3, 2),   # 14 → DEFER
            ICPScore('C', 2, 2, 2, 2, 1),   # 9  → REJECT
        ]
        summary = compute_rubric_summary(scores)
        self.assertEqual(summary['total'], 3)
        self.assertEqual(summary['proceed'], 1)
        self.assertEqual(summary['defer'], 1)
        self.assertEqual(summary['reject'], 1)

    def test_summary_empty(self):
        summary = compute_rubric_summary([])
        self.assertEqual(summary['total'], 0)
        self.assertEqual(summary['proceed_rate_pct'], 0.0)

    def test_proceed_rate_pct(self):
        scores = [ICPScore('A', 5, 5, 5, 4, 4)] * 3 + [ICPScore('B', 2, 2, 2, 2, 2)] * 1
        summary = compute_rubric_summary(scores)
        self.assertEqual(summary['proceed_rate_pct'], 75.0)


class TestICPReport(unittest.TestCase):

    def test_report_contains_prospect_name(self):
        s = ICPScore('Elena Rodriguez', 4, 4, 4, 3, 3)
        report = generate_icp_report(s)
        self.assertIn('Elena Rodriguez', report)

    def test_report_contains_verdict(self):
        s = ICPScore('Elena Rodriguez', 4, 4, 4, 3, 3)
        report = generate_icp_report(s)
        self.assertIn('PROCEED', report)

    def test_report_contains_total(self):
        s = ICPScore('x', 4, 4, 4, 3, 3)
        report = generate_icp_report(s)
        self.assertIn('18/25', report)

    def test_report_with_bc_filter_pass(self):
        s = ICPScore('x', 4, 4, 4, 3, 3)
        bc = BusinessCaseFilter('x', True, True, True)
        report = generate_icp_report(s, bc)
        self.assertIn('PASS', report)
        self.assertIn('Business Case', report)

    def test_report_with_bc_filter_fail_shows_dimensions(self):
        s = ICPScore('x', 4, 4, 4, 3, 3)
        bc = BusinessCaseFilter('x', False, True, False)
        report = generate_icp_report(s, bc)
        self.assertIn('FAIL', report)
        self.assertIn('viable', report)
        self.assertIn('achievable', report)


class TestICPGenerator(unittest.TestCase):

    def test_score_prospect_wrapper(self):
        # 4+4+3+3+4 = 18 → PROCEED boundary
        s = score_prospect('Mark Davies', 4, 4, 3, 3, 4, date='2026-06-01')
        self.assertEqual(s.total, 18)
        self.assertEqual(s.verdict, 'PROCEED')

    def test_apply_bc_filter_wrapper(self):
        bc = apply_bc_filter('Mark Davies', viable=True, desirable=False, achievable=True)
        self.assertFalse(bc.passes)

    def test_get_icp_report_wrapper(self):
        s = score_prospect('Mark Davies', 3, 3, 3, 3, 3, date='2026-06-01')
        report = get_icp_report(s)
        self.assertIn('Mark Davies', report)


if __name__ == '__main__':
    unittest.main()
