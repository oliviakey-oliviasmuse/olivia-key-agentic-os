"""Tests for Pillar 5 Agent 3 — Defect Rate Monitor."""
import unittest
from src.pillar5.defect_monitor import (
    DefectRecord,
    DEFECT_THRESHOLD,
    compute_defect_rate,
    check_threshold,
    generate_five_whys_prompt,
    generate_defect_report,
    filter_window,
)
from src.pillar5.defect_monitor_generator import create_record, log_defect, get_defect_report


# ── Helpers ────────────────────────────────────────────────────────────────

def make_records(n_defects: int, n_clean: int, process_type: str = "general") -> list:
    records = []
    for i in range(n_defects):
        records.append(DefectRecord(f"Defective-{i+1}", True, "2026-06-24",
                                    defect_description=f"Issue {i+1}", process_type=process_type))
    for i in range(n_clean):
        records.append(DefectRecord(f"Clean-{i+1}", False, "2026-06-24", process_type=process_type))
    return records


# ── Feature 1: Record Creation ─────────────────────────────────────────────

class TestRecordCreation(unittest.TestCase):

    def test_happy_path_defect_true(self):
        r = DefectRecord("Report v1", True, "2026-06-24", defect_description="Wrong format")
        self.assertTrue(r.defect)
        self.assertEqual(r.process_type, "general")
        self.assertEqual(r.defect_description, "Wrong format")

    def test_happy_path_defect_false_accepted(self):
        r = DefectRecord("Report v1", False, "2026-06-24")
        self.assertFalse(r.defect)
        self.assertEqual(r.defect_description, "")

    def test_optional_fields_default_correctly(self):
        r = DefectRecord("Report v1", True, "2026-06-24")
        self.assertEqual(r.process_type, "general")
        self.assertEqual(r.root_cause, "")
        self.assertEqual(r.corrective_action, "")

    def test_all_optional_fields_stored(self):
        r = DefectRecord(
            "Report v1", True, "2026-06-24",
            defect_description="Data error",
            process_type="proposal_turnaround",
            root_cause="Template bug",
            corrective_action="Fixed template",
        )
        self.assertEqual(r.root_cause, "Template bug")
        self.assertEqual(r.corrective_action, "Fixed template")
        self.assertEqual(r.process_type, "proposal_turnaround")

    def test_create_record_wrapper_uses_today_when_no_date(self):
        r = create_record("Report v1", False)
        self.assertRegex(r.date, r'^\d{4}-\d{2}-\d{2}$')

    def test_create_record_explicit_date(self):
        r = create_record("Report v1", True, date="2026-06-24")
        self.assertEqual(r.date, "2026-06-24")


# ── Feature 2: Gate Enforcement ────────────────────────────────────────────

class TestGateEnforcement(unittest.TestCase):

    def test_g1_empty_deliverable_name(self):
        with self.assertRaises(ValueError) as ctx:
            DefectRecord("", True, "2026-06-24")
        self.assertIn("G1", str(ctx.exception))

    def test_g2_defect_is_int_not_bool(self):
        with self.assertRaises(ValueError) as ctx:
            DefectRecord("Report", 1, "2026-06-24")
        self.assertIn("G2", str(ctx.exception))

    def test_g2_defect_is_string_not_bool(self):
        with self.assertRaises(ValueError) as ctx:
            DefectRecord("Report", "True", "2026-06-24")
        self.assertIn("G2", str(ctx.exception))

    def test_g3_invalid_date_format(self):
        with self.assertRaises(ValueError) as ctx:
            DefectRecord("Report", True, "24-06-2026")
        self.assertIn("G3", str(ctx.exception))

    def test_g3_nonsense_date(self):
        with self.assertRaises(ValueError) as ctx:
            DefectRecord("Report", True, "not-a-date")
        self.assertIn("G3", str(ctx.exception))

    def test_valid_bool_false_passes_g2(self):
        r = DefectRecord("Report", False, "2026-06-24")
        self.assertFalse(r.defect)

    def test_valid_bool_true_passes_g2(self):
        r = DefectRecord("Report", True, "2026-06-24")
        self.assertTrue(r.defect)


# ── Feature 3: Defect Rate Computation ────────────────────────────────────

class TestDefectRateComputation(unittest.TestCase):

    def test_empty_list_returns_none(self):
        self.assertIsNone(compute_defect_rate([]))

    def test_zero_defects_returns_zero(self):
        records = make_records(0, 10)
        self.assertEqual(compute_defect_rate(records), 0.0)

    def test_all_defects_returns_100(self):
        records = make_records(5, 0)
        self.assertEqual(compute_defect_rate(records), 100.0)

    def test_one_in_ten_returns_10_percent(self):
        records = make_records(1, 9)
        self.assertEqual(compute_defect_rate(records), 10.0)

    def test_one_in_twenty_returns_5_percent(self):
        records = make_records(1, 19)
        self.assertEqual(compute_defect_rate(records), 5.0)

    def test_three_in_ten_returns_30_percent(self):
        records = make_records(3, 7)
        self.assertEqual(compute_defect_rate(records), 30.0)


# ── Feature 4: Threshold Check ────────────────────────────────────────────

class TestThresholdCheck(unittest.TestCase):

    def test_none_rate_returns_no_data(self):
        self.assertEqual(check_threshold(None), "NO_DATA")

    def test_rate_below_threshold_is_ok(self):
        status = check_threshold(4.9)
        self.assertIn("OK", status)
        self.assertNotIn("WARNING", status)

    def test_rate_at_threshold_is_warning(self):
        status = check_threshold(5.0)
        self.assertIn("WARNING", status)

    def test_rate_above_threshold_is_warning(self):
        status = check_threshold(10.0)
        self.assertIn("WARNING", status)

    def test_zero_rate_is_ok(self):
        status = check_threshold(0.0)
        self.assertIn("OK", status)

    def test_custom_threshold_respected(self):
        self.assertIn("OK", check_threshold(8.0, threshold=10.0))
        self.assertIn("WARNING", check_threshold(10.0, threshold=10.0))


# ── Feature 5: 5 Whys Prompt ──────────────────────────────────────────────

class TestFiveWhysPrompt(unittest.TestCase):

    def test_prompt_contains_five_why_steps(self):
        prompt = generate_five_whys_prompt("Wrong font in report")
        self.assertIn("1. Why", prompt)
        self.assertIn("2. Why", prompt)
        self.assertIn("3. Why", prompt)
        self.assertIn("4. Why", prompt)
        self.assertIn("5. Why", prompt)

    def test_prompt_contains_defect_description(self):
        prompt = generate_five_whys_prompt("Wrong font in report")
        self.assertIn("Wrong font in report", prompt)

    def test_prompt_with_empty_description_uses_fallback(self):
        prompt = generate_five_whys_prompt("")
        self.assertIn("a defect requiring rework", prompt)

    def test_prompt_contains_root_cause_placeholder(self):
        prompt = generate_five_whys_prompt("Data error")
        self.assertIn("root cause", prompt)


# ── Feature 6: Report Generation ──────────────────────────────────────────

class TestReportGeneration(unittest.TestCase):

    def test_report_contains_process_type(self):
        records = make_records(1, 9)
        report = generate_defect_report(records, "proposal_turnaround")
        self.assertIn("proposal_turnaround", report)

    def test_report_contains_defect_rate(self):
        records = make_records(1, 9)
        report = generate_defect_report(records, "general")
        self.assertIn("10.0%", report)

    def test_report_ok_when_rate_below_threshold(self):
        records = make_records(0, 10)
        report = generate_defect_report(records, "general")
        self.assertIn("OK", report)
        self.assertNotIn("5 Whys", report)

    def test_report_warning_and_five_whys_when_rate_at_threshold(self):
        records = make_records(1, 19)  # 5% exactly
        report = generate_defect_report(records, "general")
        self.assertIn("WARNING", report)
        self.assertIn("5 Whys", report)

    def test_report_five_whys_contains_most_recent_defect_description(self):
        records = [
            DefectRecord("R1", True, "2026-06-20", defect_description="Old issue"),
            DefectRecord("R2", True, "2026-06-24", defect_description="Recent issue"),
        ] + [DefectRecord(f"C{i}", False, "2026-06-24") for i in range(18)]
        report = generate_defect_report(records, "general")
        self.assertIn("Recent issue", report)

    def test_report_empty_records_shows_na(self):
        report = generate_defect_report([], "general")
        self.assertIn("N/A", report)
        self.assertNotIn("5 Whys", report)

    def test_report_contains_total_and_defect_count(self):
        records = make_records(2, 8)  # 20% rate
        report = generate_defect_report(records, "general")
        self.assertIn("Total deliverables: 10", report)
        self.assertIn("Defects (rework): 2", report)

    def test_report_root_cause_section_present_when_triggered(self):
        records = make_records(1, 9)
        report = generate_defect_report(records, "general")
        self.assertIn("Root Cause", report)
        self.assertIn("Corrective Action", report)
        self.assertIn("SOP Update", report)


# ── Feature 7: Log Defect & Wrapper ───────────────────────────────────────

class TestLogDefectAndWrapper(unittest.TestCase):

    def test_log_defect_adds_to_empty_list(self):
        records = log_defect([], "Report v1", True, date="2026-06-24")
        self.assertEqual(len(records), 1)
        self.assertTrue(records[0].defect)

    def test_log_defect_is_immutable(self):
        original = []
        new = log_defect(original, "Report v1", True, date="2026-06-24")
        self.assertEqual(len(original), 0)
        self.assertEqual(len(new), 1)

    def test_log_defect_invalid_raises_g2(self):
        with self.assertRaises(ValueError) as ctx:
            log_defect([], "Report v1", "yes", date="2026-06-24")
        self.assertIn("G2", str(ctx.exception))

    def test_get_defect_report_filters_by_process_type(self):
        records = [
            DefectRecord("R1", True, "2026-06-24", process_type="proposal_turnaround"),
            DefectRecord("R2", True, "2026-06-24", process_type="content_production"),
            DefectRecord("R3", False, "2026-06-24", process_type="proposal_turnaround"),
        ]
        report = get_defect_report(records, process_type="proposal_turnaround")
        self.assertIn("proposal_turnaround", report)
        self.assertIn("Total deliverables: 2", report)

    def test_get_defect_report_empty_after_filter_shows_na(self):
        records = [DefectRecord("R1", True, "2026-06-24", process_type="content_production")]
        report = get_defect_report(records, process_type="proposal_turnaround")
        self.assertIn("N/A", report)

    def test_window_days_filters_old_records(self):
        records = [
            DefectRecord("Old", True, "2020-01-01"),   # very old
            DefectRecord("Recent", False, "2026-06-24"),
        ]
        windowed = filter_window(records, window_days=30)
        self.assertEqual(len(windowed), 1)
        self.assertEqual(windowed[0].deliverable_name, "Recent")


if __name__ == "__main__":
    unittest.main()
