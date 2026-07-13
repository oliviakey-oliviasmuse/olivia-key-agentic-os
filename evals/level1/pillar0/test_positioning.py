import unittest
from src.pillar0.positioning import (
    PositioningStatement,
    PositioningTest,
    CLARITY_TARGET_PCT,
    MIN_TESTS_BEFORE_LOCK,
    MIN_SPECIFICITY_MARKERS,
    TEST_PROMPT,
    SPECIFICITY_MARKERS,
    _count_specificity_markers,
    compute_clarity_score,
    check_lock_readiness,
    generate_positioning_report,
)
from src.pillar0.positioning_generator import create_statement, add_test, get_positioning_report

# Canonical valid statement used across multiple test classes —
# has role (VP Ops) + industry (capital-intensive, manufacturing) + CoPQ (cost, quality)
_VALID = (
    'I help VP Ops quantify the hidden cost of quality failure '
    'in capital-intensive manufacturing operations.'
)


class TestPositioningStatementGates(unittest.TestCase):

    def test_valid_statement(self):
        s = PositioningStatement(statement=_VALID)
        self.assertIsNotNone(s)
        self.assertEqual(s.version, '1.0')
        self.assertFalse(s.locked)

    def test_g1_empty_statement(self):
        with self.assertRaises(ValueError) as ctx:
            PositioningStatement(statement='')
        self.assertIn('G1', str(ctx.exception))

    def test_g2_statement_too_short(self):
        with self.assertRaises(ValueError) as ctx:
            PositioningStatement(statement='Cost.')
        self.assertIn('G2', str(ctx.exception))

    def test_g3_no_copq_language(self):
        with self.assertRaises(ValueError) as ctx:
            # has industry marker but no CoPQ language — fails G3 before reaching G4
            PositioningStatement(statement='I help operational leaders succeed in their organisations.')
        self.assertIn('G3', str(ctx.exception))

    def test_g3_passes_with_cost_keyword(self):
        # cost (CoPQ) + COO (role) + manufacturing, operations (industry) → G3 and G4 pass
        s = PositioningStatement(
            statement='I expose the cost of poor decisions for COO in manufacturing operations.'
        )
        self.assertIsNotNone(s)

    def test_g3_passes_with_waste_keyword(self):
        s = PositioningStatement(
            statement='I identify and eliminate waste for VP Ops in capital-intensive manufacturing.'
        )
        self.assertIsNotNone(s)

    def test_g3_passes_with_measurement_keyword(self):
        s = PositioningStatement(
            statement='I fix measurement gaps that hide losses for COO in manufacturing operations.'
        )
        self.assertIsNotNone(s)

    def test_g4_fails_with_only_one_specificity_category(self):
        # has CoPQ (cost) + industry (manufacturing) but no role/methodology/quantified → 1 category
        with self.assertRaises(ValueError) as ctx:
            PositioningStatement(
                statement='I expose the cost of poor quality in manufacturing operations.'
            )
        self.assertIn('G4', str(ctx.exception))

    def test_g4_fails_with_zero_specificity_categories(self):
        # has CoPQ language but no industry/role/methodology/quantified
        with self.assertRaises(ValueError) as ctx:
            PositioningStatement(
                statement='I help consultants reduce the cost of poor decisions they make.'
            )
        self.assertIn('G4', str(ctx.exception))

    def test_g4_passes_with_industry_and_role(self):
        s = PositioningStatement(
            statement='I quantify the cost of poor quality for COO in capital-intensive manufacturing.'
        )
        self.assertIsNotNone(s)

    def test_g4_passes_with_industry_and_methodology(self):
        s = PositioningStatement(
            statement='I apply CoPQ analysis to expose the cost of failure in manufacturing operations.'
        )
        self.assertIsNotNone(s)

    def test_g4_passes_with_industry_and_quantified(self):
        s = PositioningStatement(
            statement='I reduce the cost of poor quality by 20% in manufacturing operations.'
        )
        self.assertIsNotNone(s)

    def test_g4_error_message_contains_matched_categories(self):
        with self.assertRaises(ValueError) as ctx:
            PositioningStatement(
                statement='I expose the cost of poor quality in manufacturing operations.'
            )
        msg = str(ctx.exception)
        self.assertIn('G4', msg)
        self.assertIn('industry', msg)


class TestSpecificityMarkers(unittest.TestCase):

    def test_zero_categories(self):
        result = _count_specificity_markers('I help people solve problems.')
        self.assertEqual(result['category_count'], 0)
        self.assertFalse(result['passes'])

    def test_one_category_industry(self):
        result = _count_specificity_markers('I work in manufacturing operations.')
        self.assertEqual(result['category_count'], 1)
        self.assertFalse(result['passes'])

    def test_two_categories_industry_and_role(self):
        result = _count_specificity_markers('I help COO in manufacturing operations.')
        self.assertEqual(result['category_count'], 2)
        self.assertTrue(result['passes'])

    def test_two_categories_industry_and_methodology(self):
        result = _count_specificity_markers('I apply CoPQ in manufacturing operations.')
        self.assertEqual(result['category_count'], 2)
        self.assertTrue(result['passes'])

    def test_two_categories_industry_and_quantified(self):
        result = _count_specificity_markers('I reduce waste by 20% in manufacturing.')
        self.assertEqual(result['category_count'], 2)
        self.assertTrue(result['passes'])

    def test_all_four_categories(self):
        result = _count_specificity_markers(
            'I apply CoPQ to reduce losses by £1M for COO in capital-intensive manufacturing.'
        )
        self.assertEqual(result['category_count'], 4)
        self.assertTrue(result['passes'])

    def test_statement_specificity_method(self):
        s = PositioningStatement(_VALID)
        spec = s.specificity()
        self.assertTrue(spec['passes'])
        self.assertIn('industry', spec['matched_categories'])
        self.assertIn('role', spec['matched_categories'])


class TestPositioningStatementSubjectiveLanguage(unittest.TestCase):

    def test_no_subjective_language(self):
        # 'operations' (industry) + '20%' (quantified) → 2 categories
        s = PositioningStatement(
            statement='I quantify the cost of poor quality in operations and reduce it by 20%.'
        )
        self.assertFalse(s.has_subjective_language())

    def test_world_class_detected(self):
        # passes G4: manufacturing (industry) + COO (role)
        s = PositioningStatement(
            statement='I build world-class quality systems for COO in capital-intensive manufacturing.'
        )
        self.assertTrue(s.has_subjective_language())

    def test_best_detected(self):
        s = PositioningStatement(
            statement='I design the best measurement frameworks for COO to expose hidden losses in manufacturing.'
        )
        self.assertTrue(s.has_subjective_language())

    def test_leading_detected(self):
        s = PositioningStatement(
            statement='As a leading consultant I eliminate quality costs for COO in manufacturing operations.'
        )
        self.assertTrue(s.has_subjective_language())


class TestPositioningTest(unittest.TestCase):

    def test_valid_test_correct(self):
        t = PositioningTest(contact_name='James Okafor', date='2026-06-01', described_correctly=True)
        self.assertTrue(t.described_correctly)

    def test_valid_test_incorrect(self):
        t = PositioningTest(contact_name='Sarah Chen', date='2026-06-02', described_correctly=False)
        self.assertFalse(t.described_correctly)

    def test_g1_missing_contact_name(self):
        with self.assertRaises(ValueError) as ctx:
            PositioningTest(contact_name='', date='2026-06-01', described_correctly=True)
        self.assertIn('G1', str(ctx.exception))

    def test_g2_invalid_date(self):
        with self.assertRaises(ValueError) as ctx:
            PositioningTest(contact_name='James', date='01-06-2026', described_correctly=True)
        self.assertIn('G2', str(ctx.exception))

    def test_verbatim_response_stored(self):
        t = PositioningTest(
            contact_name='James', date='2026-06-01', described_correctly=True,
            verbatim_response='You help manufacturers find hidden quality costs'
        )
        self.assertIn('hidden quality', t.verbatim_response)

    def test_standard_prompt_is_default(self):
        t = PositioningTest(contact_name='James', date='2026-06-01', described_correctly=True)
        self.assertEqual(t.test_prompt_used, TEST_PROMPT)
        self.assertTrue(t.used_standard_prompt())

    def test_custom_prompt_stored(self):
        t = PositioningTest(
            contact_name='James', date='2026-06-01', described_correctly=True,
            test_prompt_used='Can you describe what I do?'
        )
        self.assertFalse(t.used_standard_prompt())

    def test_test_prompt_constant_value(self):
        self.assertEqual(TEST_PROMPT, "What do you think I do?")


class TestClarityScore(unittest.TestCase):

    def test_empty_tests(self):
        result = compute_clarity_score([])
        self.assertEqual(result['total_tested'], 0)
        self.assertEqual(result['clarity_score_pct'], 0.0)
        self.assertFalse(result['meets_target'])

    def test_eight_of_ten_correct(self):
        tests = (
            [PositioningTest('C', f'2026-06-{i:02d}', True) for i in range(1, 9)] +
            [PositioningTest('C', f'2026-07-{i:02d}', False) for i in range(1, 3)]
        )
        result = compute_clarity_score(tests)
        self.assertEqual(result['total_tested'], 10)
        self.assertEqual(result['described_correctly'], 8)
        self.assertEqual(result['clarity_score_pct'], 80.0)
        self.assertTrue(result['meets_target'])

    def test_exactly_80_pct_meets_target(self):
        tests = ([PositioningTest('C', '2026-06-01', True)] * 4 +
                 [PositioningTest('C', '2026-06-02', False)] * 1)
        result = compute_clarity_score(tests)
        self.assertEqual(result['clarity_score_pct'], 80.0)
        self.assertTrue(result['meets_target'])

    def test_below_80_pct_fails_target(self):
        tests = ([PositioningTest('C', '2026-06-01', True)] * 7 +
                 [PositioningTest('C', '2026-06-02', False)] * 3)
        result = compute_clarity_score(tests)
        self.assertFalse(result['meets_target'])

    def test_all_correct(self):
        tests = [PositioningTest('C', f'2026-06-{i:02d}', True) for i in range(1, 6)]
        result = compute_clarity_score(tests)
        self.assertEqual(result['clarity_score_pct'], 100.0)
        self.assertTrue(result['meets_target'])

    def test_non_standard_prompt_flagged(self):
        t1 = PositioningTest('James', '2026-06-01', True)
        t2 = PositioningTest('Sarah', '2026-06-02', True, test_prompt_used='Tell me what you do?')
        result = compute_clarity_score([t1, t2])
        self.assertIn('Sarah', result['non_standard_prompt_contacts'])
        self.assertNotIn('James', result['non_standard_prompt_contacts'])

    def test_all_standard_prompts_empty_list(self):
        tests = [PositioningTest('C', f'2026-06-{i:02d}', True) for i in range(1, 4)]
        result = compute_clarity_score(tests)
        self.assertEqual(result['non_standard_prompt_contacts'], [])


class TestLockReadiness(unittest.TestCase):

    def _good_statement(self):
        return PositioningStatement(
            'I quantify the cost of poor quality for VP Ops in capital-intensive manufacturing.'
        )

    def _passing_tests(self, n=5):
        return [PositioningTest('C', f'2026-06-{i:02d}', True) for i in range(1, n + 1)]

    def test_ready_to_lock(self):
        defects = check_lock_readiness(self._good_statement(), self._passing_tests(5))
        self.assertEqual(defects, [])

    def test_ps1_fewer_than_5_tests(self):
        defects = check_lock_readiness(self._good_statement(), self._passing_tests(3))
        self.assertIn('PS1', defects)

    def test_ps2_clarity_below_target(self):
        tests = ([PositioningTest('C', '2026-06-01', True)] * 3 +
                 [PositioningTest('C', '2026-06-02', False)] * 7)
        defects = check_lock_readiness(self._good_statement(), tests)
        self.assertIn('PS2', defects)

    def test_ps3_subjective_language(self):
        # passes G4: VP Ops (role) + manufacturing (industry)
        s = PositioningStatement(
            'I build world-class measurement systems for VP Ops that expose '
            'the cost of failure in manufacturing.'
        )
        defects = check_lock_readiness(s, self._passing_tests(5))
        self.assertIn('PS3', defects)

    def test_multiple_defects_simultaneously(self):
        defects = check_lock_readiness(self._good_statement(), [])
        self.assertIn('PS1', defects)
        self.assertIn('PS2', defects)


class TestPositioningReport(unittest.TestCase):

    def test_report_contains_statement(self):
        s = PositioningStatement(
            'I expose the cost of poor quality for COO in manufacturing operations.'
        )
        report = generate_positioning_report(s, [])
        self.assertIn('I expose the cost of poor quality', report)

    def test_report_contains_clarity_score(self):
        s = PositioningStatement(
            'I expose the hidden cost of poor quality for VP Ops in manufacturing operations.'
        )
        tests = [PositioningTest('A', '2026-06-01', True)] * 5
        report = generate_positioning_report(s, tests)
        self.assertIn('Clarity score:', report)
        self.assertIn('100.0%', report)

    def test_report_contains_test_prompt(self):
        s = PositioningStatement(_VALID)
        report = generate_positioning_report(s, [])
        self.assertIn('What do you think I do?', report)

    def test_report_shows_specificity_check(self):
        s = PositioningStatement(_VALID)
        report = generate_positioning_report(s, [])
        self.assertIn('Specificity Check', report)
        self.assertIn('Passes generalist test: Yes', report)

    def test_report_flags_subjective_language(self):
        s = PositioningStatement(
            'I build world-class systems for COO that expose the cost of failure in manufacturing.'
        )
        report = generate_positioning_report(s, [])
        self.assertIn('WARNING', report)

    def test_report_shows_defects(self):
        s = PositioningStatement(
            'I expose the cost of poor quality for COO in manufacturing operations.'
        )
        report = generate_positioning_report(s, [])
        self.assertIn('PS1', report)
        self.assertIn('PS2', report)

    def test_report_shows_test_log(self):
        s = PositioningStatement(
            'I expose the hidden cost of poor quality for VP Ops in manufacturing.'
        )
        t = PositioningTest('James Okafor', '2026-06-01', True, 'helps with quality costs')
        report = generate_positioning_report(s, [t])
        self.assertIn('James Okafor', report)
        self.assertIn('Yes', report)

    def test_report_flags_non_standard_prompt(self):
        s = PositioningStatement(_VALID)
        t = PositioningTest('Sarah', '2026-06-01', True, test_prompt_used='Tell me about your work.')
        report = generate_positioning_report(s, [t])
        self.assertIn('Non-standard prompt', report)
        self.assertIn('Sarah', report)

    def test_report_prompt_standard_column_in_log(self):
        s = PositioningStatement(_VALID)
        t1 = PositioningTest('James', '2026-06-01', True)
        t2 = PositioningTest('Sarah', '2026-06-02', False, test_prompt_used='Other prompt?')
        report = generate_positioning_report(s, [t1, t2])
        self.assertIn('Prompt Standard', report)


class TestPositioningGenerator(unittest.TestCase):

    def test_create_statement_wrapper(self):
        s = create_statement(
            'I expose the hidden cost of quality failure for VP Ops in capital-intensive operations.'
        )
        self.assertEqual(s.version, '1.0')
        self.assertFalse(s.locked)

    def test_add_test_wrapper(self):
        t = add_test('Elena Rodriguez', '2026-06-05', True)
        self.assertEqual(t.contact_name, 'Elena Rodriguez')
        self.assertTrue(t.described_correctly)
        self.assertEqual(t.test_prompt_used, TEST_PROMPT)

    def test_get_report_wrapper(self):
        s = create_statement(
            'I expose the hidden cost of poor quality for COO in manufacturing operations.'
        )
        report = get_positioning_report(s, [])
        self.assertIn('Positioning Statement Report', report)


if __name__ == '__main__':
    unittest.main()
