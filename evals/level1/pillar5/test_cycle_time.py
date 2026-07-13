"""Tests for Pillar 5 Agent 2 — Process Cycle Time Tracker."""
import unittest
from src.pillar5.cycle_time import (
    CycleTimeRecord,
    VALID_PROCESS_TYPES,
    compute_average_cycle_time,
    compute_reduction,
    check_target,
    generate_cycle_time_report,
    linear_regression,
)
from src.pillar5.cycle_time_generator import create_record, get_report, log_cycle_time


# ── Helpers ────────────────────────────────────────────────────────────────

def make_proposal_records():
    return [
        create_record('proposal_turnaround', '2026-06-01', '2026-06-05', 'Acme'),
        create_record('proposal_turnaround', '2026-06-10', '2026-06-15', 'Beta'),
    ]


# ── Feature 1: Record Creation ─────────────────────────────────────────────

class TestRecordCreation(unittest.TestCase):

    def test_happy_path_cycle_days_computed(self):
        r = create_record('proposal_turnaround', '2026-06-01', '2026-06-05', 'Acme Proposal')
        self.assertEqual(r.process_type, 'proposal_turnaround')
        self.assertEqual(r.cycle_days, 4)

    def test_same_day_zero_cycle(self):
        r = create_record('content_production', '2026-06-01', '2026-06-01')
        self.assertEqual(r.cycle_days, 0)

    def test_all_valid_process_types_accepted(self):
        for pt in VALID_PROCESS_TYPES:
            r = create_record(pt, '2026-06-01', '2026-06-10')
            self.assertEqual(r.process_type, pt)

    def test_default_instance_name(self):
        r = create_record('client_onboarding', '2026-06-01', '2026-06-10')
        self.assertEqual(r.instance_name, 'Instance 1')

    def test_custom_instance_name(self):
        r = create_record('proposal_turnaround', '2026-06-01', '2026-06-05', 'Acme Proposal')
        self.assertEqual(r.instance_name, 'Acme Proposal')


# ── Feature 2: Gate Enforcement ────────────────────────────────────────────

class TestGateEnforcement(unittest.TestCase):

    def test_g1_invalid_process_type(self):
        with self.assertRaises(ValueError) as ctx:
            create_record('invalid', '2026-06-01', '2026-06-05')
        self.assertIn('G1', str(ctx.exception))

    def test_g2_invalid_date_format(self):
        with self.assertRaises(ValueError) as ctx:
            create_record('proposal_turnaround', '2026-99-99', '2026-06-05')
        self.assertIn('G2', str(ctx.exception))

    def test_g2_empty_start_date(self):
        with self.assertRaises(ValueError) as ctx:
            create_record('proposal_turnaround', '', '2026-06-05')
        self.assertIn('G2', str(ctx.exception))

    def test_g2_empty_end_date(self):
        with self.assertRaises(ValueError) as ctx:
            create_record('proposal_turnaround', '2026-06-01', '')
        self.assertIn('G2', str(ctx.exception))

    def test_g3_end_before_start(self):
        with self.assertRaises(ValueError) as ctx:
            create_record('proposal_turnaround', '2026-06-05', '2026-06-01')
        self.assertIn('G3', str(ctx.exception))

    def test_g3_boundary_same_day_passes(self):
        r = create_record('proposal_turnaround', '2026-06-05', '2026-06-05')
        self.assertEqual(r.cycle_days, 0)


# ── Feature 3: Average Cycle Time ─────────────────────────────────────────

class TestAverageCycleTime(unittest.TestCase):

    def test_two_records_average(self):
        records = make_proposal_records()
        avg = compute_average_cycle_time(records)
        self.assertEqual(avg, 4.5)

    def test_single_record_average(self):
        records = [create_record('proposal_turnaround', '2026-06-01', '2026-06-09')]
        self.assertEqual(compute_average_cycle_time(records), 8.0)

    def test_empty_list_returns_none(self):
        self.assertIsNone(compute_average_cycle_time([]))

    def test_zero_cycle_day_included_in_average(self):
        records = [
            create_record('content_production', '2026-06-01', '2026-06-01'),
            create_record('content_production', '2026-06-01', '2026-06-11'),
        ]
        self.assertEqual(compute_average_cycle_time(records), 5.0)


# ── Feature 4: Reduction Computation ──────────────────────────────────────

class TestReductionComputation(unittest.TestCase):

    def test_20_percent_reduction(self):
        self.assertEqual(compute_reduction(10.0, 8.0), 20.0)

    def test_50_percent_reduction(self):
        self.assertEqual(compute_reduction(10.0, 5.0), 50.0)

    def test_zero_reduction(self):
        self.assertEqual(compute_reduction(10.0, 10.0), 0.0)

    def test_baseline_zero_returns_zero(self):
        self.assertEqual(compute_reduction(0.0, 8.0), 0.0)

    def test_negative_reduction_cycle_longer_than_baseline(self):
        result = compute_reduction(10.0, 12.0)
        self.assertLess(result, 0)


# ── Feature 5: Target Check ────────────────────────────────────────────────

class TestTargetCheck(unittest.TestCase):

    def test_on_track_when_reduction_meets_target(self):
        self.assertEqual(check_target(10.0, 8.0, 20.0), 'ON TRACK')

    def test_on_track_when_reduction_exceeds_target(self):
        self.assertEqual(check_target(10.0, 5.0, 20.0), 'ON TRACK')

    def test_warning_when_reduction_below_target(self):
        self.assertEqual(check_target(10.0, 9.5, 20.0), 'WARNING – reduction not on track')

    def test_no_data_when_baseline_zero(self):
        self.assertEqual(check_target(0.0, 8.0, 20.0), 'NO_DATA')

    def test_exactly_at_target_is_on_track(self):
        self.assertEqual(check_target(10.0, 8.0, 20.0), 'ON TRACK')


# ── Feature 6: Report Generation ──────────────────────────────────────────

class TestReportGeneration(unittest.TestCase):

    def test_report_contains_process_type(self):
        records = make_proposal_records()
        report = get_report(records, 'proposal_turnaround', baseline=10.0)
        self.assertIn('proposal_turnaround', report)

    def test_report_contains_average_cycle_time(self):
        records = make_proposal_records()
        report = get_report(records, 'proposal_turnaround', baseline=10.0)
        self.assertIn('4.5 days', report)

    def test_report_status_on_track(self):
        records = make_proposal_records()
        report = get_report(records, 'proposal_turnaround', baseline=10.0, target_reduction_pct=20.0)
        self.assertIn('ON TRACK', report)

    def test_report_contains_instance_names(self):
        records = make_proposal_records()
        report = get_report(records, 'proposal_turnaround', baseline=10.0)
        self.assertIn('Acme', report)
        self.assertIn('Beta', report)

    def test_report_warning_when_not_on_track(self):
        records = [create_record('proposal_turnaround', '2026-06-01', '2026-06-02')]
        report = get_report(records, 'proposal_turnaround', baseline=1.0, target_reduction_pct=50.0)
        self.assertIn('WARNING', report)

    def test_report_no_records_message(self):
        report = get_report([], 'content_production', baseline=10.0)
        self.assertIn('No records found', report)

    def test_report_filters_by_process_type(self):
        records = [
            create_record('proposal_turnaround', '2026-06-01', '2026-06-05', 'Prop1'),
            create_record('content_production', '2026-06-01', '2026-06-20', 'Content1'),
        ]
        report = get_report(records, 'proposal_turnaround', baseline=10.0)
        self.assertIn('Prop1', report)
        self.assertNotIn('Content1', report)

    def test_regression_output(self):
        records = [
            create_record('proposal_turnaround', '2026-06-01', '2026-06-05'),  # 4 days
            create_record('proposal_turnaround', '2026-06-10', '2026-06-13'),  # 3 days
            create_record('proposal_turnaround', '2026-06-20', '2026-06-22'),  # 2 days
        ]
        report = get_report(
            records, 'proposal_turnaround',
            baseline=10.0, target_reduction_pct=20.0, include_regression=True,
        )
        self.assertIn('Trend Analysis', report)
        self.assertIn('slope', report)
        self.assertIn('R²', report)
        self.assertIn('p-value', report)

    def test_regression_omitted_when_flag_false(self):
        records = [
            create_record('proposal_turnaround', '2026-06-01', '2026-06-05'),
            create_record('proposal_turnaround', '2026-06-10', '2026-06-13'),
            create_record('proposal_turnaround', '2026-06-20', '2026-06-22'),
        ]
        report = get_report(records, 'proposal_turnaround', baseline=10.0)
        self.assertNotIn('Trend Analysis', report)

    def test_regression_omitted_when_fewer_than_3_records(self):
        records = [
            create_record('proposal_turnaround', '2026-06-01', '2026-06-05'),
            create_record('proposal_turnaround', '2026-06-10', '2026-06-13'),
        ]
        report = get_report(records, 'proposal_turnaround', baseline=10.0, include_regression=True)
        self.assertNotIn('Trend Analysis', report)


# ── Feature 8: Linear Regression ──────────────────────────────────────────

class TestLinearRegression(unittest.TestCase):

    def test_perfect_negative_slope(self):
        xs = [1, 2, 3, 4, 5]
        ys = [4, 3, 2, 1, 0]
        slope, intercept, r2, p = linear_regression(xs, ys)
        self.assertAlmostEqual(slope, -1.0)
        self.assertAlmostEqual(intercept, 5.0)
        self.assertAlmostEqual(r2, 1.0)
        self.assertIsNotNone(p)

    def test_fewer_than_2_points_returns_none(self):
        slope, intercept, r2, p = linear_regression([1], [1])
        self.assertIsNone(slope)

    def test_vertical_line_returns_none(self):
        slope, intercept, r2, p = linear_regression([1, 1, 1], [1, 2, 3])
        self.assertIsNone(slope)

    def test_flat_line_slope_zero(self):
        xs = [1, 2, 3]
        ys = [5, 5, 5]
        slope, intercept, r2, p = linear_regression(xs, ys)
        self.assertAlmostEqual(slope, 0.0)
        self.assertAlmostEqual(intercept, 5.0)
        self.assertAlmostEqual(r2, 0.0)

    def test_positive_slope(self):
        xs = [1, 2, 3]
        ys = [1, 2, 3]
        slope, intercept, r2, p = linear_regression(xs, ys)
        self.assertAlmostEqual(slope, 1.0)
        self.assertAlmostEqual(r2, 1.0)


# ── Feature 7: Log Cycle Time ─────────────────────────────────────────────

class TestLogCycleTime(unittest.TestCase):

    def test_log_adds_record_to_empty_list(self):
        records = log_cycle_time([], 'proposal_turnaround', '2026-06-01', '2026-06-05', 'Acme')
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].cycle_days, 4)

    def test_log_appends_to_existing_list(self):
        records = log_cycle_time([], 'proposal_turnaround', '2026-06-01', '2026-06-05')
        records = log_cycle_time(records, 'proposal_turnaround', '2026-06-10', '2026-06-15')
        self.assertEqual(len(records), 2)

    def test_log_does_not_mutate_original_list(self):
        original = []
        new_records = log_cycle_time(original, 'proposal_turnaround', '2026-06-01', '2026-06-05')
        self.assertEqual(len(original), 0)
        self.assertEqual(len(new_records), 1)

    def test_log_invalid_type_raises_g1(self):
        with self.assertRaises(ValueError) as ctx:
            log_cycle_time([], 'invalid_type', '2026-06-01', '2026-06-05')
        self.assertIn('G1', str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
