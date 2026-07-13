import os
import tempfile
import unittest
from src.pillar7.framework_library import (
    FrameworkEntry,
    VALID_LICENSING,
    increment_version,
    list_entries,
    search_entries,
)
from src.pillar7.framework_library_generator import store_entry


def _entry(**kwargs):
    defaults = dict(
        name='SIPOC Template',
        problem_solved='Maps service delivery chain',
        inputs=['Client data', 'Scope brief'],
        process_steps=['Define scope', 'Map suppliers', 'List outputs'],
        outputs=['SIPOC diagram'],
        quality_criteria=['All 5 columns complete'],
        licensing_status='Proprietary',
        version='1.0',
        date='2026-06-25',
    )
    defaults.update(kwargs)
    return FrameworkEntry(**defaults)


class TestFrameworkEntryCreation(unittest.TestCase):
    def test_valid_entry_defaults(self):
        e = _entry()
        self.assertEqual(e.name, 'SIPOC Template')
        self.assertEqual(e.version, '1.0')
        self.assertEqual(e.licensing_status, 'Proprietary')

    def test_all_valid_licensing_statuses(self):
        for status in VALID_LICENSING:
            e = _entry(licensing_status=status)
            self.assertEqual(e.licensing_status, status)

    def test_custom_version_stored(self):
        e = _entry(version='2.3')
        self.assertEqual(e.version, '2.3')

    def test_default_version_is_1_0(self):
        e = FrameworkEntry(
            name='Test', problem_solved='x',
            inputs=['a'], process_steps=['b'],
            outputs=['c'], quality_criteria=['d'],
            licensing_status='Open',
        )
        self.assertEqual(e.version, '1.0')

    def test_default_date_is_set(self):
        e = FrameworkEntry(
            name='Test', problem_solved='x',
            inputs=['a'], process_steps=['b'],
            outputs=['c'], quality_criteria=['d'],
            licensing_status='Open',
        )
        self.assertIsNotNone(e.date)
        self.assertEqual(len(e.date), 10)

    def test_multiple_steps_stored(self):
        e = _entry(process_steps=['Step 1', 'Step 2', 'Step 3'])
        self.assertEqual(len(e.process_steps), 3)


class TestGateEnforcement(unittest.TestCase):
    def test_g1_missing_name(self):
        with self.assertRaises(ValueError) as ctx:
            _entry(name='')
        self.assertIn('G1', str(ctx.exception))

    def test_g2_missing_problem(self):
        with self.assertRaises(ValueError) as ctx:
            _entry(problem_solved='')
        self.assertIn('G2', str(ctx.exception))

    def test_g3_empty_inputs(self):
        with self.assertRaises(ValueError) as ctx:
            _entry(inputs=[])
        self.assertIn('G3', str(ctx.exception))

    def test_g4_empty_process_steps(self):
        with self.assertRaises(ValueError) as ctx:
            _entry(process_steps=[])
        self.assertIn('G4', str(ctx.exception))

    def test_g5_empty_outputs(self):
        with self.assertRaises(ValueError) as ctx:
            _entry(outputs=[])
        self.assertIn('G5', str(ctx.exception))

    def test_g6_empty_quality_criteria(self):
        with self.assertRaises(ValueError) as ctx:
            _entry(quality_criteria=[])
        self.assertIn('G6', str(ctx.exception))

    def test_g7_invalid_licensing(self):
        with self.assertRaises(ValueError) as ctx:
            _entry(licensing_status='Invalid')
        self.assertIn('G7', str(ctx.exception))

    def test_g7_case_sensitive(self):
        # 'proprietary' (lowercase) is not in VALID_LICENSING
        with self.assertRaises(ValueError) as ctx:
            _entry(licensing_status='proprietary')
        self.assertIn('G7', str(ctx.exception))


class TestMarkdownGeneration(unittest.TestCase):
    def test_header_contains_name(self):
        md = _entry().to_markdown()
        self.assertIn('# Framework – SIPOC Template', md)

    def test_version_and_date_in_header(self):
        md = _entry(version='2.1', date='2026-06-25').to_markdown()
        self.assertIn('Version: 2.1', md)
        self.assertIn('2026-06-25', md)

    def test_licensing_in_header(self):
        md = _entry(licensing_status='Open').to_markdown()
        self.assertIn('Licensing: Open', md)

    def test_problem_solved_present(self):
        md = _entry().to_markdown()
        self.assertIn('Maps service delivery chain', md)

    def test_inputs_as_bullet_list(self):
        md = _entry(inputs=['Input A', 'Input B']).to_markdown()
        self.assertIn('- Input A', md)
        self.assertIn('- Input B', md)

    def test_process_steps_numbered(self):
        md = _entry(process_steps=['Step A', 'Step B']).to_markdown()
        self.assertIn('1. Step A', md)
        self.assertIn('2. Step B', md)

    def test_outputs_as_bullet_list(self):
        md = _entry().to_markdown()
        self.assertIn('- SIPOC diagram', md)

    def test_quality_criteria_as_bullet_list(self):
        md = _entry().to_markdown()
        self.assertIn('- All 5 columns complete', md)

    def test_date_truncated_to_10_chars(self):
        # Even if date were a full ISO timestamp, only first 10 chars shown
        e = _entry(date='2026-06-25T10:30:00')
        md = e.to_markdown()
        self.assertIn('2026-06-25', md)
        self.assertNotIn('T10:30', md)


class TestVersionIncrement(unittest.TestCase):
    def test_increment_minor_1_0(self):
        self.assertEqual(increment_version('1.0'), '1.1')

    def test_increment_minor_2_5(self):
        self.assertEqual(increment_version('2.5'), '2.6')

    def test_increment_minor_0_9(self):
        self.assertEqual(increment_version('0.9'), '0.10')

    def test_increment_major_preserved(self):
        self.assertEqual(increment_version('3.0'), '3.1')

    def test_increment_fallback_for_malformed(self):
        self.assertEqual(increment_version('invalid'), '1.0')


class TestListEntries(unittest.TestCase):
    def test_empty_list_returns_sentinel(self):
        self.assertEqual(list_entries([]), "No entries found.")

    def test_single_entry_in_table(self):
        result = list_entries([_entry()])
        self.assertIn('SIPOC Template', result)
        self.assertIn('Proprietary', result)
        self.assertIn('| Name |', result)

    def test_multiple_entries_all_listed(self):
        e1 = _entry(name='SIPOC')
        e2 = _entry(name='CTQ Tree', licensing_status='Licensed')
        result = list_entries([e1, e2])
        self.assertIn('SIPOC', result)
        self.assertIn('CTQ Tree', result)
        self.assertIn('Licensed', result)


class TestSearchEntries(unittest.TestCase):
    def test_search_by_problem_solved(self):
        e = _entry()
        results = search_entries([e], 'delivery')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, 'SIPOC Template')

    def test_search_by_name(self):
        e = _entry()
        results = search_entries([e], 'sipoc')
        self.assertEqual(len(results), 1)

    def test_search_by_input(self):
        e = _entry(inputs=['defect rate data', 'process map'])
        results = search_entries([e], 'defect')
        self.assertEqual(len(results), 1)

    def test_search_by_process_step(self):
        e = _entry(process_steps=['Measure baseline', 'Analyse root cause'])
        results = search_entries([e], 'baseline')
        self.assertEqual(len(results), 1)

    def test_search_no_match(self):
        e = _entry()
        results = search_entries([e], 'xyznotfound')
        self.assertEqual(len(results), 0)

    def test_search_case_insensitive(self):
        e = _entry(name='SIPOC Template')
        results = search_entries([e], 'SIPOC')
        self.assertEqual(len(results), 1)

    def test_search_multiple_entries_filtered(self):
        e1 = _entry(name='SIPOC', problem_solved='maps delivery chain')
        e2 = _entry(name='CTQ Tree', problem_solved='captures voice of customer')
        results = search_entries([e1, e2], 'voice')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, 'CTQ Tree')


class TestStoreEntry(unittest.TestCase):
    def test_store_returns_markdown(self):
        e = _entry()
        result = store_entry(e)
        self.assertIn('SIPOC Template', result)

    def test_store_appends_to_file(self):
        e = _entry()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            path = f.name
        try:
            store_entry(e, library_path=path)
            with open(path, encoding='utf-8') as f:
                content = f.read()
            self.assertIn('SIPOC Template', content)
            self.assertIn('Maps service delivery chain', content)
        finally:
            os.unlink(path)

    def test_store_no_path_no_file_written(self):
        e = _entry()
        result = store_entry(e, library_path=None)
        self.assertIn('SIPOC Template', result)


if __name__ == "__main__":
    unittest.main()
