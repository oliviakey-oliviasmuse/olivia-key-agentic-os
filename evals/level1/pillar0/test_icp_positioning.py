import unittest
import tempfile
import os
from src.pillar0.icp_positioning import (
    ICP,
    VoiceRules,
    Positioning,
    is_in_icp,
    is_in_icp_detailed,
    validate_content,
    check_positioning_match,
    generate_authority_report,
    to_yaml,
    from_yaml,
)
from src.pillar0.icp_positioning_generator import (
    create_positioning,
    get_icp,
    get_positioning_statement,
    get_voice_rules,
    validate_prospect,
    validate_content_text,
    write_yaml_file,
    load_yaml_file,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_icp(**overrides):
    defaults = dict(
        industries=['Manufacturing', 'Aerospace'],
        min_company_size=200,
        max_company_size=5000,
        arr_min=20_000_000,
        arr_max=500_000_000,
        roles=['VP Ops', 'COO', 'Plant Manager'],
        geography=['UK', 'Europe'],
    )
    defaults.update(overrides)
    return ICP(**defaults)


def make_voice(**overrides):
    defaults = dict(
        vocabulary_use=['CoPQ', 'hidden factory', 'rework', 'scrap', 'downtime'],
        vocabulary_avoid=['revolutionary', 'game-changer', 'best-in-class', 'synergy'],
        tone_adjectives=['professional', 'factual', 'slightly contrarian'],
    )
    defaults.update(overrides)
    return VoiceRules(**defaults)


def make_positioning(**overrides):
    defaults = dict(
        statement='We systematically remove waste and reduce variation in capital-intensive operations.',
        icp=make_icp(),
        voice=make_voice(),
        anti_icp=['Pre-revenue startups', 'Pure SaaS companies'],
        version='1.0',
    )
    defaults.update(overrides)
    return Positioning(**defaults)


def in_icp_prospect():
    return {
        'industry': 'Manufacturing',
        'company_size': 1000,
        'arr': 100_000_000,
        'role': 'COO',
        'geography': 'UK',
    }


# ---------------------------------------------------------------------------
# Gate enforcement — ICP
# ---------------------------------------------------------------------------

class TestICPGates(unittest.TestCase):

    def test_valid_icp_constructs(self):
        icp = make_icp()
        self.assertEqual(icp.industries, ['Manufacturing', 'Aerospace'])

    def test_g1_empty_industries(self):
        with self.assertRaises(ValueError) as ctx:
            make_icp(industries=[])
        self.assertIn('G1', str(ctx.exception))

    def test_g1_empty_roles(self):
        with self.assertRaises(ValueError) as ctx:
            make_icp(roles=[])
        self.assertIn('G1', str(ctx.exception))

    def test_g1_empty_geography(self):
        with self.assertRaises(ValueError) as ctx:
            make_icp(geography=[])
        self.assertIn('G1', str(ctx.exception))

    def test_g1_invalid_size_range(self):
        with self.assertRaises(ValueError) as ctx:
            make_icp(min_company_size=5000, max_company_size=200)
        self.assertIn('min_company_size must be < max_company_size', str(ctx.exception))

    def test_g1_equal_size_range(self):
        with self.assertRaises(ValueError):
            make_icp(min_company_size=500, max_company_size=500)

    def test_g4_invalid_arr_range(self):
        with self.assertRaises(ValueError) as ctx:
            make_icp(arr_min=500_000_000, arr_max=20_000_000)
        self.assertIn('G4', str(ctx.exception))

    def test_g4_equal_arr_range(self):
        with self.assertRaises(ValueError):
            make_icp(arr_min=20_000_000, arr_max=20_000_000)


# ---------------------------------------------------------------------------
# Gate enforcement — VoiceRules
# ---------------------------------------------------------------------------

class TestVoiceRulesGates(unittest.TestCase):

    def test_valid_voice_constructs(self):
        v = make_voice()
        self.assertIn('CoPQ', v.vocabulary_use)

    def test_g3_empty_vocabulary_use(self):
        with self.assertRaises(ValueError) as ctx:
            make_voice(vocabulary_use=[])
        self.assertIn('G3', str(ctx.exception))

    def test_g3_empty_vocabulary_avoid(self):
        with self.assertRaises(ValueError) as ctx:
            make_voice(vocabulary_avoid=[])
        self.assertIn('G3', str(ctx.exception))

    def test_g3_empty_tone_adjectives(self):
        with self.assertRaises(ValueError) as ctx:
            make_voice(tone_adjectives=[])
        self.assertIn('G3', str(ctx.exception))


# ---------------------------------------------------------------------------
# Gate enforcement — Positioning
# ---------------------------------------------------------------------------

class TestPositioningGates(unittest.TestCase):

    def test_valid_positioning_constructs(self):
        p = make_positioning()
        self.assertEqual(p.version, '1.0')

    def test_g2_empty_statement(self):
        with self.assertRaises(ValueError) as ctx:
            make_positioning(statement='')
        self.assertIn('G2', str(ctx.exception))

    def test_g2_none_statement(self):
        with self.assertRaises(ValueError):
            make_positioning(statement=None)

    def test_anti_icp_defaults_to_empty(self):
        p = Positioning(
            statement='We remove waste.',
            icp=make_icp(),
            voice=make_voice(),
        )
        self.assertEqual(p.anti_icp, [])


# ---------------------------------------------------------------------------
# is_in_icp — hard gate
# ---------------------------------------------------------------------------

class TestIsInICP(unittest.TestCase):

    def setUp(self):
        self.p = make_positioning()

    def test_happy_path_all_criteria_pass(self):
        self.assertTrue(is_in_icp(self.p, in_icp_prospect()))

    def test_wrong_industry_fails(self):
        prospect = {**in_icp_prospect(), 'industry': 'Retail'}
        self.assertFalse(is_in_icp(self.p, prospect))

    def test_wrong_role_fails(self):
        prospect = {**in_icp_prospect(), 'role': 'Marketing Manager'}
        self.assertFalse(is_in_icp(self.p, prospect))

    def test_wrong_geography_fails(self):
        prospect = {**in_icp_prospect(), 'geography': 'USA'}
        self.assertFalse(is_in_icp(self.p, prospect))

    def test_arr_below_min_fails(self):
        prospect = {**in_icp_prospect(), 'arr': 1_000_000}
        self.assertFalse(is_in_icp(self.p, prospect))

    def test_arr_above_max_fails(self):
        prospect = {**in_icp_prospect(), 'arr': 600_000_000}
        self.assertFalse(is_in_icp(self.p, prospect))

    def test_arr_at_min_boundary_passes(self):
        prospect = {**in_icp_prospect(), 'arr': 20_000_000}
        self.assertTrue(is_in_icp(self.p, prospect))

    def test_arr_at_max_boundary_passes(self):
        prospect = {**in_icp_prospect(), 'arr': 500_000_000}
        self.assertTrue(is_in_icp(self.p, prospect))

    def test_company_size_at_min_boundary_passes(self):
        prospect = {**in_icp_prospect(), 'company_size': 200}
        self.assertTrue(is_in_icp(self.p, prospect))

    def test_company_size_below_min_fails(self):
        prospect = {**in_icp_prospect(), 'company_size': 50}
        self.assertFalse(is_in_icp(self.p, prospect))

    def test_second_industry_in_list_passes(self):
        prospect = {**in_icp_prospect(), 'industry': 'Aerospace'}
        self.assertTrue(is_in_icp(self.p, prospect))

    def test_second_role_in_list_passes(self):
        prospect = {**in_icp_prospect(), 'role': 'Plant Manager'}
        self.assertTrue(is_in_icp(self.p, prospect))


# ---------------------------------------------------------------------------
# is_in_icp_detailed — failure reasons
# ---------------------------------------------------------------------------

class TestIsInICPDetailed(unittest.TestCase):

    def setUp(self):
        self.p = make_positioning()

    def test_all_pass_returns_empty_failures(self):
        result = is_in_icp_detailed(self.p, in_icp_prospect())
        self.assertTrue(result['pass'])
        self.assertEqual(result['failures'], [])

    def test_multiple_failures_all_reported(self):
        prospect = {
            'industry': 'Retail',
            'company_size': 50,
            'arr': 1_000_000,
            'role': 'Marketing Manager',
            'geography': 'USA',
        }
        result = is_in_icp_detailed(self.p, prospect)
        self.assertFalse(result['pass'])
        self.assertGreater(len(result['failures']), 1)

    def test_single_failure_identified(self):
        prospect = {**in_icp_prospect(), 'industry': 'Retail'}
        result = is_in_icp_detailed(self.p, prospect)
        self.assertFalse(result['pass'])
        self.assertTrue(any('industry' in f for f in result['failures']))


# ---------------------------------------------------------------------------
# validate_content — voice gate (P2 G12)
# ---------------------------------------------------------------------------

class TestValidateContent(unittest.TestCase):

    def setUp(self):
        self.p = make_positioning()

    def test_clean_text_passes(self):
        result = validate_content(self.p, 'We measure CoPQ and reduce hidden factory waste.')
        self.assertTrue(result['pass'])
        self.assertEqual(result['violations'], [])

    def test_banned_word_fails(self):
        result = validate_content(self.p, 'This revolutionary approach transforms operations.')
        self.assertFalse(result['pass'])
        self.assertIn('revolutionary', result['violations'])

    def test_multiple_violations_all_returned(self):
        result = validate_content(self.p, 'This revolutionary game-changer delivers synergy.')
        self.assertFalse(result['pass'])
        self.assertGreaterEqual(len(result['violations']), 2)

    def test_case_insensitive_detection(self):
        result = validate_content(self.p, 'A REVOLUTIONARY product for industry.')
        self.assertFalse(result['pass'])
        self.assertIn('revolutionary', result['violations'])

    def test_empty_text_passes(self):
        result = validate_content(self.p, '')
        self.assertTrue(result['pass'])


# ---------------------------------------------------------------------------
# check_positioning_match — P3 proposal gate
# ---------------------------------------------------------------------------

class TestCheckPositioningMatch(unittest.TestCase):

    def setUp(self):
        self.p = make_positioning()

    def test_exact_match_passes(self):
        self.assertTrue(check_positioning_match(self.p.statement, self.p)['pass'])

    def test_case_insensitive_match_passes(self):
        self.assertTrue(check_positioning_match(self.p.statement.upper(), self.p)['pass'])

    def test_whitespace_trimmed_match_passes(self):
        self.assertTrue(check_positioning_match('  ' + self.p.statement + '  ', self.p)['pass'])

    def test_different_statement_fails(self):
        self.assertFalse(check_positioning_match('We help businesses grow.', self.p)['pass'])

    def test_result_includes_version_and_authority(self):
        result = check_positioning_match(self.p.statement, self.p)
        self.assertIn('version', result)
        self.assertIn('authority', result)
        self.assertEqual(result['authority'], self.p.statement)


# ---------------------------------------------------------------------------
# generate_authority_report
# ---------------------------------------------------------------------------

class TestGenerateAuthorityReport(unittest.TestCase):

    def setUp(self):
        self.p = make_positioning()
        self.report = generate_authority_report(self.p)

    def test_report_contains_version(self):
        self.assertIn('Version 1.0', self.report)

    def test_report_contains_positioning_statement(self):
        self.assertIn('capital-intensive operations', self.report)

    def test_report_contains_industries(self):
        self.assertIn('Manufacturing', self.report)

    def test_report_contains_roles(self):
        self.assertIn('COO', self.report)

    def test_report_contains_voice_use(self):
        self.assertIn('CoPQ', self.report)

    def test_report_contains_voice_avoid(self):
        self.assertIn('revolutionary', self.report)

    def test_report_contains_anti_icp(self):
        self.assertIn('Pre-revenue startups', self.report)

    def test_report_no_anti_icp_shows_none_defined(self):
        p = make_positioning(anti_icp=[])
        report = generate_authority_report(p)
        self.assertIn('None defined', report)


# ---------------------------------------------------------------------------
# YAML round-trip
# ---------------------------------------------------------------------------

class TestYAMLRoundTrip(unittest.TestCase):

    def setUp(self):
        self.p = make_positioning()

    def test_to_yaml_contains_positioning(self):
        yaml_str = to_yaml(self.p)
        self.assertIn('positioning:', yaml_str)
        self.assertIn('capital-intensive', yaml_str)

    def test_to_yaml_contains_industries(self):
        yaml_str = to_yaml(self.p)
        self.assertIn('Manufacturing', yaml_str)

    def test_from_yaml_restores_statement(self):
        yaml_str = to_yaml(self.p)
        restored = from_yaml(yaml_str)
        self.assertEqual(restored.statement, self.p.statement)

    def test_from_yaml_restores_icp_industries(self):
        yaml_str = to_yaml(self.p)
        restored = from_yaml(yaml_str)
        self.assertEqual(restored.icp.industries, self.p.icp.industries)

    def test_from_yaml_restores_voice_rules(self):
        yaml_str = to_yaml(self.p)
        restored = from_yaml(yaml_str)
        self.assertEqual(restored.voice.vocabulary_avoid, self.p.voice.vocabulary_avoid)

    def test_from_yaml_restores_anti_icp(self):
        yaml_str = to_yaml(self.p)
        restored = from_yaml(yaml_str)
        self.assertEqual(restored.anti_icp, self.p.anti_icp)


# ---------------------------------------------------------------------------
# File persistence (write_yaml_file / load_yaml_file)
# ---------------------------------------------------------------------------

class TestFilePersistence(unittest.TestCase):

    def test_write_and_load_round_trip(self):
        p = make_positioning()
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False, mode='w') as f:
            path = f.name
        try:
            write_yaml_file(p, path)
            loaded = load_yaml_file(path)
            self.assertEqual(loaded.statement, p.statement)
            self.assertEqual(loaded.icp.industries, p.icp.industries)
            self.assertEqual(loaded.voice.vocabulary_use, p.voice.vocabulary_use)
        finally:
            os.unlink(path)

    def test_write_creates_valid_yaml(self):
        p = make_positioning()
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False, mode='w') as f:
            path = f.name
        try:
            write_yaml_file(p, path)
            content = open(path, encoding='utf-8').read()
            self.assertIn('positioning:', content)
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# Generator wrappers
# ---------------------------------------------------------------------------

class TestGeneratorWrappers(unittest.TestCase):

    def setUp(self):
        self.p = make_positioning()

    def test_get_icp_returns_dict(self):
        result = get_icp(self.p)
        self.assertIn('industries', result)
        self.assertIn('roles', result)
        self.assertEqual(result['arr_min'], 20_000_000)

    def test_get_positioning_statement(self):
        stmt = get_positioning_statement(self.p)
        self.assertEqual(stmt, self.p.statement)

    def test_get_voice_rules_returns_dict(self):
        result = get_voice_rules(self.p)
        self.assertIn('vocabulary_use', result)
        self.assertIn('vocabulary_avoid', result)
        self.assertIn('CoPQ', result['vocabulary_use'])

    def test_validate_prospect_pass(self):
        result = validate_prospect(self.p, in_icp_prospect())
        self.assertTrue(result['pass'])
        self.assertIsNone(result['reason'])

    def test_validate_prospect_fail_returns_reason(self):
        bad = {**in_icp_prospect(), 'industry': 'Retail'}
        result = validate_prospect(self.p, bad)
        self.assertFalse(result['pass'])
        self.assertIsNotNone(result['reason'])
        self.assertIn('industry', result['reason'])

    def test_validate_content_text_clean(self):
        result = validate_content_text(self.p, 'Measuring CoPQ across operations.')
        self.assertTrue(result['pass'])

    def test_create_positioning_builds_correctly(self):
        p = create_positioning(
            industries=['Aerospace'],
            min_company_size=200,
            max_company_size=5000,
            arr_min=20_000_000,
            arr_max=500_000_000,
            roles=['VP Ops'],
            geography=['UK'],
            positioning_statement='We eliminate waste in aerospace operations.',
            vocabulary_use=['CoPQ'],
            vocabulary_avoid=['revolutionary'],
            tone_adjectives=['professional'],
        )
        self.assertEqual(p.icp.industries, ['Aerospace'])
        self.assertEqual(p.statement, 'We eliminate waste in aerospace operations.')


if __name__ == '__main__':
    unittest.main()
