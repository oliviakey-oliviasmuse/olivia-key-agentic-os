"""Tests for Pillar 5 Agent 0 — 5Ms Allocation Tracker.

Note on test data for OK-status assertions:
    With tolerance=0.10, OK range is [0.90, 1.10]. Data like 35/40 = 87.5%
    falls UNDER threshold (< 0.90) — tests use ≥90% values where OK is asserted.
"""
import unittest
from src.pillar5.five_ms_tracker import (
    FiveMsRecord,
    compute_utilisation,
    compute_status,
    check_g2_warning,
    summarise_five_ms,
    generate_allocation_log,
)
from src.pillar5.five_ms_tracker_generator import create_record, generate_report


# ── Helpers ────────────────────────────────────────────────────────────────

def all_ok_record() -> FiveMsRecord:
    """All 5 Ms at ~95% utilisation — well within OK band."""
    return FiveMsRecord(
        week_start='2026-06-24',
        manpower_allocated=38, manpower_available=40,      # 95%
        materials_allocated=230, materials_available=250,  # 92%
        machinery_allocated=0.95, machinery_available=1.0, # 95%
        minutes_allocated=23, minutes_available=25,        # 92%
        money_allocated=330, money_available=350,          # 94.3%
    )


def constraint_record() -> FiveMsRecord:
    """Manpower OVER, Materials and Machinery UNDER."""
    return FiveMsRecord(
        week_start='2026-06-24',
        manpower_allocated=45, manpower_available=40,      # 112.5% → OVER
        materials_allocated=100, materials_available=250,  # 40% → UNDER
        machinery_allocated=0.5, machinery_available=1.0,  # 50% → UNDER
    )


# ── Feature 1: Record Creation & G1 Gate ──────────────────────────────────

class TestFiveMsRecordCreation(unittest.TestCase):

    def test_valid_record_created(self):
        rec = FiveMsRecord(week_start='2026-06-24')
        self.assertEqual(rec.week_start, '2026-06-24')
        self.assertEqual(rec.manpower_allocated, 0.0)

    def test_all_fields_stored(self):
        rec = FiveMsRecord(
            week_start='2026-06-24',
            manpower_allocated=38, manpower_available=40,
            money_allocated=330, money_available=350,
        )
        self.assertEqual(rec.manpower_allocated, 38)
        self.assertEqual(rec.money_available, 350)

    def test_g1_empty_week_start_raises(self):
        with self.assertRaises(ValueError) as ctx:
            FiveMsRecord(week_start='')
        self.assertIn('G1', str(ctx.exception))
        self.assertIn('week_start', str(ctx.exception))

    def test_g1_invalid_date_format_raises(self):
        with self.assertRaises(ValueError) as ctx:
            FiveMsRecord(week_start='24-06-2026')
        self.assertIn('G1', str(ctx.exception))
        self.assertIn('YYYY-MM-DD', str(ctx.exception))

    def test_g1_nonsense_date_raises(self):
        with self.assertRaises(ValueError) as ctx:
            FiveMsRecord(week_start='2026-99-99')
        self.assertIn('G1', str(ctx.exception))

    def test_g1_valid_date_passes(self):
        rec = FiveMsRecord(week_start='2026-01-01')
        self.assertEqual(rec.week_start, '2026-01-01')


# ── Feature 2: Utilisation Computation ────────────────────────────────────

class TestUtilisationComputation(unittest.TestCase):

    def test_normal_utilisation(self):
        self.assertAlmostEqual(compute_utilisation(38, 40), 0.95)

    def test_full_utilisation(self):
        self.assertEqual(compute_utilisation(40, 40), 1.0)

    def test_over_utilisation(self):
        self.assertAlmostEqual(compute_utilisation(45, 40), 1.125)

    def test_zero_available_returns_none(self):
        self.assertIsNone(compute_utilisation(35, 0))

    def test_zero_allocated_zero_available_returns_none(self):
        self.assertIsNone(compute_utilisation(0, 0))

    def test_zero_allocated_nonzero_available_returns_zero(self):
        self.assertEqual(compute_utilisation(0, 40), 0.0)


# ── Feature 3: Status Computation ─────────────────────────────────────────

class TestStatusComputation(unittest.TestCase):

    def test_none_utilisation_returns_no_data(self):
        self.assertEqual(compute_status(None), 'NO_DATA')

    def test_ok_status_at_full_utilisation(self):
        self.assertEqual(compute_status(1.0), 'OK')

    def test_ok_status_at_lower_bound(self):
        self.assertEqual(compute_status(0.90), 'OK')

    def test_under_status_just_below_lower_bound(self):
        self.assertEqual(compute_status(0.89), 'UNDER')

    def test_ok_status_at_upper_bound(self):
        self.assertEqual(compute_status(1.10), 'OK')

    def test_over_status_just_above_upper_bound(self):
        self.assertEqual(compute_status(1.11), 'OVER')

    def test_custom_tolerance_respected(self):
        self.assertEqual(compute_status(0.85, tolerance=0.20), 'OK')
        self.assertEqual(compute_status(0.79, tolerance=0.20), 'UNDER')
        self.assertEqual(compute_status(1.21, tolerance=0.20), 'OVER')

    def test_over_at_112_percent(self):
        self.assertEqual(compute_status(1.125), 'OVER')

    def test_under_at_40_percent(self):
        self.assertEqual(compute_status(0.40), 'UNDER')

    def test_under_at_50_percent(self):
        self.assertEqual(compute_status(0.50), 'UNDER')


# ── Feature 4: G2 Soft Gate ───────────────────────────────────────────────

class TestG2SoftGate(unittest.TestCase):

    def test_no_warning_when_all_5_ms_populated(self):
        rec = all_ok_record()
        self.assertIsNone(check_g2_warning(rec))

    def test_no_warning_when_exactly_3_ms_populated(self):
        rec = FiveMsRecord(
            week_start='2026-06-24',
            manpower_allocated=38, manpower_available=40,
            materials_allocated=230, materials_available=250,
            machinery_allocated=0.95, machinery_available=1.0,
        )
        self.assertIsNone(check_g2_warning(rec))

    def test_warning_when_only_1_m_populated(self):
        rec = FiveMsRecord(week_start='2026-06-24', manpower_allocated=38, manpower_available=40)
        warning = check_g2_warning(rec)
        self.assertIsNotNone(warning)
        self.assertIn('G2', warning)
        self.assertIn('only 1', warning)

    def test_warning_when_only_2_ms_populated(self):
        rec = FiveMsRecord(
            week_start='2026-06-24',
            manpower_allocated=38, manpower_available=40,
            materials_allocated=230, materials_available=250,
        )
        warning = check_g2_warning(rec)
        self.assertIsNotNone(warning)
        self.assertIn('only 2', warning)

    def test_g2_warning_appears_in_report(self):
        rec = FiveMsRecord(week_start='2026-06-24', manpower_allocated=38, manpower_available=40)
        log = generate_allocation_log(rec)
        self.assertIn('G2', log)
        self.assertIn('WARNING', log)


# ── Feature 5: Summarise Five Ms ──────────────────────────────────────────

class TestSummariseFiveMs(unittest.TestCase):

    def test_all_ok_when_within_tolerance(self):
        summary = summarise_five_ms(all_ok_record())
        self.assertEqual(summary['ms_summary']['Manpower']['status'], 'OK')
        self.assertEqual(summary['ms_summary']['Materials']['status'], 'OK')
        self.assertEqual(summary['ms_summary']['Machinery']['status'], 'OK')
        self.assertEqual(summary['constraints']['OVER'], [])
        self.assertEqual(summary['constraints']['UNDER'], [])

    def test_utilisation_values_computed(self):
        summary = summarise_five_ms(all_ok_record())
        self.assertAlmostEqual(summary['ms_summary']['Manpower']['utilisation'], 0.95)

    def test_over_constraint_flagged(self):
        summary = summarise_five_ms(constraint_record())
        self.assertIn('Manpower', summary['constraints']['OVER'])

    def test_under_constraints_flagged(self):
        summary = summarise_five_ms(constraint_record())
        self.assertIn('Materials', summary['constraints']['UNDER'])
        self.assertIn('Machinery', summary['constraints']['UNDER'])

    def test_no_data_when_m_not_set(self):
        rec = FiveMsRecord(week_start='2026-06-24')
        summary = summarise_five_ms(rec)
        self.assertEqual(summary['ms_summary']['Manpower']['status'], 'NO_DATA')

    def test_custom_tolerance_applied(self):
        rec = FiveMsRecord(
            week_start='2026-06-24',
            manpower_allocated=42, manpower_available=40,  # 105% — OVER at 2% tolerance
        )
        summary = summarise_five_ms(rec, tolerance=0.02)
        self.assertEqual(summary['ms_summary']['Manpower']['status'], 'OVER')


# ── Feature 6: Report Generation ──────────────────────────────────────────

class TestReportGeneration(unittest.TestCase):

    def test_report_contains_week_date(self):
        log = generate_allocation_log(all_ok_record())
        self.assertIn('Week 2026-06-24', log)

    def test_report_contains_all_five_ms(self):
        log = generate_allocation_log(all_ok_record())
        for m in ['Manpower', 'Materials', 'Machinery', 'Minutes', 'Money']:
            self.assertIn(m, log)

    def test_report_no_constraints_when_all_ok(self):
        log = generate_allocation_log(all_ok_record())
        self.assertIn('None: All within tolerance', log)

    def test_report_shows_ok_status(self):
        log = generate_allocation_log(all_ok_record())
        self.assertIn('OK', log)

    def test_report_shows_over_constraint(self):
        log = generate_allocation_log(constraint_record())
        self.assertIn('OVER', log)
        self.assertIn('Manpower', log)
        self.assertIn('action required', log)

    def test_report_shows_under_constraint(self):
        log = generate_allocation_log(constraint_record())
        self.assertIn('UNDER', log)
        self.assertIn('idle capacity', log)

    def test_report_shows_utilisation_percentage(self):
        log = generate_allocation_log(all_ok_record())
        self.assertIn('95.0%', log)

    def test_report_g2_warning_when_partial(self):
        rec = FiveMsRecord(week_start='2026-06-24', manpower_allocated=38, manpower_available=40)
        log = generate_allocation_log(rec)
        self.assertIn('G2 WARNING', log)

    def test_report_no_g2_warning_when_full(self):
        log = generate_allocation_log(all_ok_record())
        self.assertNotIn('G2 WARNING', log)


# ── Feature 7: Wrapper ────────────────────────────────────────────────────

class TestWrapper(unittest.TestCase):

    def test_create_record_returns_five_ms_record(self):
        rec = create_record('2026-06-24', manpower_allocated=38, manpower_available=40)
        self.assertIsInstance(rec, FiveMsRecord)
        self.assertEqual(rec.week_start, '2026-06-24')
        self.assertEqual(rec.manpower_allocated, 38)

    def test_create_record_g1_propagates(self):
        with self.assertRaises(ValueError) as ctx:
            create_record('')
        self.assertIn('G1', str(ctx.exception))

    def test_generate_report_returns_string(self):
        rec = create_record('2026-06-24', manpower_allocated=38, manpower_available=40)
        report = generate_report(rec)
        self.assertIsInstance(report, str)
        self.assertIn('Week 2026-06-24', report)

    def test_generate_report_custom_tolerance(self):
        rec = create_record(
            '2026-06-24',
            manpower_allocated=42, manpower_available=40,  # 105%
        )
        report_strict = generate_report(rec, tolerance=0.02)
        report_lenient = generate_report(rec, tolerance=0.10)
        self.assertIn('OVER', report_strict)
        self.assertIn('OK', report_lenient)

    def test_full_trigger_phrase_example(self):
        """Matches the spec's example trigger phrase (illustrative — no status assertions)."""
        rec = create_record(
            '2026-06-24',
            manpower_allocated=35, manpower_available=40,
            materials_allocated=200, materials_available=250,
            machinery_allocated=0.8, machinery_available=1.0,
            minutes_allocated=20, minutes_available=25,
            money_allocated=300, money_available=350,
        )
        report = generate_report(rec)
        self.assertIn('Week 2026-06-24', report)
        self.assertIn('Manpower', report)
        self.assertIn('Materials', report)
        self.assertIn('Machinery', report)
        self.assertIn('Minutes', report)
        self.assertIn('Money', report)


if __name__ == '__main__':
    unittest.main()
