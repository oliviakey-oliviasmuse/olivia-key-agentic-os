import unittest
from src.pillar3.discovery_analyser import (
    parse_notes,
    build_fishbone,
    estimate_copq,
    validate_business_case,
    build_analyser_report,
    FISHBONE_CATEGORIES,
    DEFAULT_COPQ_BENCHMARK,
)


class TestParseNotes(unittest.TestCase):
    def test_parse_notes_returns_dict(self):
        notes = "Sample call notes"
        result = parse_notes(notes)
        self.assertIsInstance(result, dict)
        self.assertIn('pain_points', result)
        self.assertIn('metrics', result)
        self.assertIn('decision_criteria', result)

    def test_parse_notes_extracts_pain(self):
        notes = "We have high rework and scrap rates. Warranty claims are up."
        result = parse_notes(notes)
        self.assertIn('operational waste', result['pain_points'])
        self.assertIn('external failure', result['pain_points'])


class TestFishbone(unittest.TestCase):
    def test_build_fishbone_returns_dict(self):
        notes = "This is a test"
        result = build_fishbone(notes)
        self.assertIsInstance(result, dict)
        for cat in FISHBONE_CATEGORIES:
            self.assertIn(cat, result)

    def test_build_fishbone_captures_causes(self):
        notes = "Operators skip logging. Machines need calibration. Material variability."
        result = build_fishbone(notes)
        self.assertGreater(len(result['Manpower']), 0)
        self.assertGreater(len(result['Machine']), 0)
        self.assertGreater(len(result['Material']), 0)

    def test_build_fishbone_handles_empty_notes(self):
        notes = ""
        result = build_fishbone(notes)
        self.assertIsInstance(result, dict)
        for cat in FISHBONE_CATEGORIES:
            self.assertEqual(result[cat], [])


class TestCoPQ(unittest.TestCase):
    def test_estimate_copq_requires_revenue(self):
        with self.assertRaises(ValueError) as ctx:
            estimate_copq("Sample", revenue=None)
        self.assertIn('Revenue is required', str(ctx.exception))

    def test_estimate_copq_returns_dict_with_revenue(self):
        result = estimate_copq("Sample", revenue=100_000_000)
        self.assertIn('internal_failure', result)
        self.assertIn('external_failure', result)
        self.assertIn('appraisal', result)
        self.assertIn('prevention', result)
        self.assertIn('total', result)

    def test_estimate_copq_calculates_correctly(self):
        result = estimate_copq("", revenue=200_000_000)
        self.assertEqual(result['total'], 30_000_000)  # 200M × 0.15

    def test_estimate_copq_allocation_sums_to_total(self):
        result = estimate_copq("", revenue=100_000_000)
        total = result['internal_failure'] + result['external_failure'] + result['appraisal'] + result['prevention']
        self.assertEqual(total, result['total'])


class TestBusinessCase(unittest.TestCase):
    def test_validate_business_case_returns_dict(self):
        notes = "Rework is a problem. Budget approved. Priority. Scope defined."
        result = validate_business_case(notes)
        self.assertIn('criteria', result)
        self.assertIn('overall', result)
        self.assertIn('reason', result)
        self.assertIn('warning', result)

    def test_validate_business_case_passes(self):
        notes = "Rework costs are high. This is a top priority. We have scope and support."
        result = validate_business_case(notes)
        self.assertTrue(result['overall'])

    def test_validate_business_case_fails_missing_viable(self):
        notes = "This is a nice idea. Budget approved. Scope defined."
        result = validate_business_case(notes)
        self.assertFalse(result['criteria']['viable'])
        self.assertFalse(result['overall'])

    def test_validate_business_case_fails_missing_desirable(self):
        notes = "We have rework. Scope defined. But no urgency."
        result = validate_business_case(notes)
        self.assertFalse(result['criteria']['desirable'])
        self.assertFalse(result['overall'])

    def test_validate_business_case_fails_missing_achievable(self):
        # No achievable keywords (scope/capacity/deliver/implementation/support/resources)
        notes = "We have rework. This is a top priority. But we are not ready."
        result = validate_business_case(notes)
        self.assertFalse(result['criteria']['achievable'])
        self.assertFalse(result['overall'])

    def test_manual_override_returns_pass_and_warning(self):
        result = validate_business_case("", manual_override=True)
        self.assertTrue(result['overall'])
        self.assertEqual(result['reason'], 'Manually overridden by user')
        self.assertIn('manually overridden', result['warning'])

    def test_manual_override_returns_warning(self):
        result = validate_business_case("", manual_override=True)
        self.assertIn('warning', result)


class TestAnalyserReport(unittest.TestCase):
    def test_build_report_raises_on_empty_notes(self):
        with self.assertRaises(ValueError) as ctx:
            build_analyser_report("")
        self.assertIn('too short', str(ctx.exception))

    def test_build_report_raises_on_short_notes(self):
        with self.assertRaises(ValueError) as ctx:
            build_analyser_report("Hello")
        self.assertIn('too short', str(ctx.exception))

    def test_build_report_returns_dict(self):
        notes = "Rework is 18%. Budget approved. Priority. Scope defined."
        result = build_analyser_report(notes, revenue=100_000_000)
        self.assertIn('fishbone', result)
        self.assertIn('copq', result)
        self.assertIn('business_case', result)
        self.assertIn('next_steps', result)
        self.assertIn('parsed', result)

    def test_build_report_proceed_on_pass(self):
        notes = "Rework is 18%. Budget approved. Top priority. Scope defined."
        result = build_analyser_report(notes, revenue=100_000_000)
        self.assertEqual(result['next_steps'], 'Proceed to proposal (Agent 3)')

    def test_build_report_defers_on_fail(self):
        notes = "We have a small issue, no urgency, no budget."
        result = build_analyser_report(notes, revenue=100_000_000)
        self.assertIn('Address missing business case criteria', result['next_steps'])

    def test_build_report_includes_copq_with_revenue(self):
        notes = "Rework issues on line 3. Scope and support available."
        result = build_analyser_report(notes, revenue=150_000_000)
        self.assertEqual(result['copq']['total'], 22_500_000)  # 150M × 0.15


if __name__ == "__main__":
    unittest.main()
