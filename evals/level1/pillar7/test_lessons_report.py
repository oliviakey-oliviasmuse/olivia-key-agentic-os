import os
import tempfile
import unittest
from src.pillar7.lessons_report import LessonsReport, generate_lessons_report
from src.pillar7.lessons_report_generator import log_to_lessons_log


def _report(**kwargs):
    defaults = dict(
        engagement_name='Acme Aerospace',
        client_name='Acme',
        close_date='2026-06-25',
        what_worked=['Daily defect huddles', 'Real-time logging'],
        what_didnt=['Training schedule'],
        root_cause='Training scheduled during peak production',
        corrective_action='Move training to off-peak hours',
        sop_update_required=False,
        report_date='2026-06-27',
    )
    defaults.update(kwargs)
    return LessonsReport(**defaults)


class TestLessonsReportCreation(unittest.TestCase):
    def test_valid_report_no_sop(self):
        r = _report()
        self.assertEqual(r.engagement_name, 'Acme Aerospace')
        self.assertEqual(len(r.what_worked), 2)
        self.assertFalse(r.sop_update_required)

    def test_valid_report_with_sop(self):
        r = _report(sop_update_required=True, sop_update_description='Update training SOP')
        self.assertTrue(r.sop_update_required)
        self.assertEqual(r.sop_update_description, 'Update training SOP')

    def test_lessons_derived_when_not_provided(self):
        r = _report()
        self.assertIsNotNone(r.lessons_learned)
        self.assertGreater(len(r.lessons_learned), 0)

    def test_lessons_first_item_is_continue(self):
        r = _report()
        self.assertTrue(r.lessons_learned[0].startswith('Continue:'))

    def test_lessons_second_item_is_improve(self):
        r = _report()
        self.assertTrue(r.lessons_learned[1].startswith('Improve:'))

    def test_explicit_lessons_not_overridden(self):
        explicit = ['My custom lesson']
        r = _report(lessons_learned=explicit)
        self.assertEqual(r.lessons_learned, explicit)

    def test_default_report_date_is_set(self):
        r = LessonsReport(
            engagement_name='Test', client_name='Client',
            close_date='2026-06-25',
            what_worked=['x'], what_didnt=['y'],
            root_cause='z', corrective_action='a',
            sop_update_required=False,
        )
        self.assertIsNotNone(r.report_date)
        self.assertEqual(len(r.report_date), 10)


class TestGateEnforcement(unittest.TestCase):
    def test_g1_missing_engagement(self):
        with self.assertRaises(ValueError) as ctx:
            _report(engagement_name='')
        self.assertIn('G1', str(ctx.exception))

    def test_g2_missing_client(self):
        with self.assertRaises(ValueError) as ctx:
            _report(client_name='')
        self.assertIn('G2', str(ctx.exception))

    def test_g3_invalid_date(self):
        with self.assertRaises(ValueError) as ctx:
            _report(close_date='2026-99-99')
        self.assertIn('G3', str(ctx.exception))

    def test_g3_malformed_date(self):
        with self.assertRaises(ValueError) as ctx:
            _report(close_date='not-a-date')
        self.assertIn('G3', str(ctx.exception))

    def test_g4_empty_what_worked(self):
        with self.assertRaises(ValueError) as ctx:
            _report(what_worked=[])
        self.assertIn('G4', str(ctx.exception))

    def test_g5_empty_what_didnt(self):
        with self.assertRaises(ValueError) as ctx:
            _report(what_didnt=[])
        self.assertIn('G5', str(ctx.exception))

    def test_g6_missing_root_cause(self):
        with self.assertRaises(ValueError) as ctx:
            _report(root_cause='')
        self.assertIn('G6', str(ctx.exception))

    def test_g7_missing_corrective_action(self):
        with self.assertRaises(ValueError) as ctx:
            _report(corrective_action='')
        self.assertIn('G7', str(ctx.exception))

    def test_sop_update_true_requires_description(self):
        with self.assertRaises(ValueError) as ctx:
            _report(sop_update_required=True, sop_update_description=None)
        self.assertIn('sop_update_description required', str(ctx.exception))

    def test_sop_update_false_no_description_ok(self):
        r = _report(sop_update_required=False, sop_update_description=None)
        self.assertFalse(r.sop_update_required)


class TestDaysSinceClose(unittest.TestCase):
    def test_days_since_close(self):
        r = _report(close_date='2026-06-01', report_date='2026-06-10')
        self.assertEqual(r.days_since_close(as_of='2026-06-10'), 9)

    def test_days_since_close_zero(self):
        r = _report()
        self.assertEqual(r.days_since_close(as_of='2026-06-25'), 0)

    def test_is_overdue_within_limit(self):
        # report 2 days after close → not overdue
        r = _report(close_date='2026-06-25', report_date='2026-06-27')
        self.assertFalse(r.is_overdue())

    def test_is_overdue_at_boundary(self):
        # exactly 5 days → not overdue (> not >=)
        r = _report(close_date='2026-06-20', report_date='2026-06-25')
        self.assertFalse(r.is_overdue())

    def test_is_overdue_past_limit(self):
        # 6 days after close → overdue (L1 defect)
        r = _report(close_date='2026-06-01', report_date='2026-06-07')
        self.assertTrue(r.is_overdue())


class TestReportGeneration(unittest.TestCase):
    def test_report_contains_engagement_name(self):
        r = _report()
        md = generate_lessons_report(r)
        self.assertIn('Acme Aerospace', md)

    def test_report_contains_client(self):
        r = _report()
        md = generate_lessons_report(r)
        self.assertIn('Acme', md)

    def test_report_contains_what_worked(self):
        r = _report()
        md = generate_lessons_report(r)
        self.assertIn('Daily defect huddles', md)

    def test_report_contains_what_didnt(self):
        r = _report()
        md = generate_lessons_report(r)
        self.assertIn('Training schedule', md)

    def test_report_contains_root_cause(self):
        r = _report()
        md = generate_lessons_report(r)
        self.assertIn('Training scheduled during peak production', md)

    def test_report_sop_yes_with_description(self):
        r = _report(sop_update_required=True, sop_update_description='Update training SOP')
        md = generate_lessons_report(r)
        self.assertIn('SOP Update Required?', md)
        self.assertIn('Yes', md)
        self.assertIn('Update training SOP', md)

    def test_report_sop_no(self):
        r = _report(sop_update_required=False)
        md = generate_lessons_report(r)
        self.assertIn('No', md)

    def test_report_l1_warning_when_overdue(self):
        r = _report(close_date='2026-06-01', report_date='2026-06-10')
        md = generate_lessons_report(r)
        self.assertIn('L1 WARNING', md)

    def test_report_no_l1_warning_when_on_time(self):
        r = _report(close_date='2026-06-25', report_date='2026-06-27')
        md = generate_lessons_report(r)
        self.assertNotIn('L1 WARNING', md)

    def test_report_contains_lessons_learned_section(self):
        r = _report()
        md = generate_lessons_report(r)
        self.assertIn('## Lessons Learned', md)
        self.assertIn('Continue:', md)


class TestLessonsLog(unittest.TestCase):
    def test_log_appends_to_file(self):
        r = _report(sop_update_required=True, sop_update_description='Update SOP')
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            path = f.name
        try:
            log_to_lessons_log(r, path)
            with open(path, encoding='utf-8') as f:
                content = f.read()
            self.assertIn('Acme Aerospace', content)
            self.assertIn('Update SOP', content)
        finally:
            os.unlink(path)

    def test_log_returns_entry_string(self):
        r = _report()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            path = f.name
        try:
            entry = log_to_lessons_log(r, path)
            self.assertIn('Acme Aerospace', entry)
        finally:
            os.unlink(path)

    def test_log_sop_no_when_false(self):
        r = _report(sop_update_required=False)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            path = f.name
        try:
            entry = log_to_lessons_log(r, path)
            self.assertIn('SOP update: No', entry)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
