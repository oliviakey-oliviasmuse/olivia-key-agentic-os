import unittest
from src.pillar0.discovery_tracker import (
    DiscoveryConversation,
    TARGET_CONVERSATIONS,
    collect_icp_language,
    check_readiness,
    generate_discovery_report,
)
from src.pillar0.discovery_tracker_generator import log_conversation, get_discovery_report

# htdq default reflects the correct Hero/Treasure/Dragon/Quest framing
_HTDQ_EXAMPLE = (
    'Hero: senior ops leader firefighting daily. '
    'Treasure: operational clarity and control. '
    'Dragon: invisible quality costs nobody can quantify. '
    'Quest: becoming the executive who fixed what others ignored.'
)


def _make_conversation(
    contact='James Okafor',
    date='2026-06-01',
    situation='Plant running at 65% OEE',
    complication='No measurement system to identify root cause',
    question='Where is the hidden factory costing us?',
    htdq=_HTDQ_EXAMPLE,
    dragon=None,
    icp_language=None,
    copq_estimate=None,
):
    return DiscoveryConversation(
        contact_name=contact,
        date=date,
        situation=situation,
        complication=complication,
        question=question,
        htdq=htdq,
        dragon=dragon,
        icp_language=icp_language or ['we just accept the rework'],
        copq_estimate=copq_estimate,
    )


class TestDiscoveryConversationGates(unittest.TestCase):

    def test_valid_conversation(self):
        c = _make_conversation()
        self.assertEqual(c.contact_name, 'James Okafor')
        self.assertTrue(c.has_icp_language())

    def test_g1_missing_contact_name(self):
        with self.assertRaises(ValueError) as ctx:
            _make_conversation(contact='')
        self.assertIn('G1', str(ctx.exception))

    def test_g2_invalid_date(self):
        with self.assertRaises(ValueError) as ctx:
            _make_conversation(date='01/06/2026')
        self.assertIn('G2', str(ctx.exception))

    def test_g3_missing_situation(self):
        with self.assertRaises(ValueError) as ctx:
            _make_conversation(situation='')
        self.assertIn('G3', str(ctx.exception))

    def test_g4_missing_complication(self):
        with self.assertRaises(ValueError) as ctx:
            _make_conversation(complication='')
        self.assertIn('G4', str(ctx.exception))

    def test_g5_missing_question(self):
        with self.assertRaises(ValueError) as ctx:
            _make_conversation(question='')
        self.assertIn('G5', str(ctx.exception))

    def test_g6_missing_htdq(self):
        with self.assertRaises(ValueError) as ctx:
            _make_conversation(htdq='')
        self.assertIn('G6', str(ctx.exception))

    def test_icp_language_optional(self):
        c = DiscoveryConversation(
            contact_name='James',
            date='2026-06-01',
            situation='OEE at 65%',
            complication='No measurement system',
            question='Where is the waste?',
            htdq='How do we quantify the hidden factory?',
        )
        self.assertFalse(c.has_icp_language())

    def test_copq_estimate_optional(self):
        c = _make_conversation()
        self.assertFalse(c.has_copq_estimate())

    def test_copq_estimate_stored(self):
        c = _make_conversation(copq_estimate=450000.0)
        self.assertTrue(c.has_copq_estimate())
        self.assertEqual(c.copq_estimate, 450000.0)


class TestCollectICPLanguage(unittest.TestCase):

    def test_collects_all_phrases(self):
        c1 = _make_conversation(icp_language=['we just accept the rework', 'nobody measures it'])
        c2 = _make_conversation(contact='Sarah', date='2026-06-02', icp_language=['the defects are invisible'])
        phrases = collect_icp_language([c1, c2])
        self.assertEqual(len(phrases), 3)
        self.assertIn('we just accept the rework', phrases)
        self.assertIn('the defects are invisible', phrases)

    def test_empty_list(self):
        self.assertEqual(collect_icp_language([]), [])

    def test_skips_conversations_with_no_phrases(self):
        c = DiscoveryConversation(
            contact_name='James', date='2026-06-01',
            situation='x', complication='y', question='z', htdq='w',
        )
        self.assertEqual(collect_icp_language([c]), [])


class TestCheckReadiness(unittest.TestCase):

    def test_not_ready_below_target(self):
        convs = [_make_conversation(contact=f'C{i}', date=f'2026-06-{i:02d}') for i in range(1, 4)]
        r = check_readiness(convs)
        self.assertFalse(r['ready_to_lock'])
        self.assertEqual(r['total_conversations'], 3)

    def test_ready_at_target(self):
        convs = [_make_conversation(contact=f'C{i}', date=f'2026-06-{i:02d}') for i in range(1, 6)]
        r = check_readiness(convs)
        self.assertTrue(r['ready_to_lock'])
        self.assertEqual(r['total_conversations'], TARGET_CONVERSATIONS)

    def test_ready_above_target(self):
        convs = [_make_conversation(contact=f'C{i}', date=f'2026-06-{i:02d}') for i in range(1, 8)]
        r = check_readiness(convs)
        self.assertTrue(r['ready_to_lock'])

    def test_d1_flagged_for_missing_icp_language(self):
        c_no_phrases = DiscoveryConversation(
            contact_name='Mark', date='2026-06-01',
            situation='x', complication='y', question='z', htdq='w',
        )
        r = check_readiness([c_no_phrases])
        self.assertIn('Mark', r['d1_contacts'])

    def test_d2_flagged_for_missing_copq(self):
        c = _make_conversation()
        r = check_readiness([c])
        self.assertIn('James Okafor', r['d2_contacts'])

    def test_d2_cleared_when_copq_present(self):
        c = _make_conversation(copq_estimate=200000.0)
        r = check_readiness([c])
        self.assertNotIn('James Okafor', r['d2_contacts'])

    def test_empty_list(self):
        r = check_readiness([])
        self.assertFalse(r['ready_to_lock'])
        self.assertEqual(r['total_conversations'], 0)
        self.assertEqual(r['all_icp_phrases'], [])


class TestDiscoveryReport(unittest.TestCase):

    def test_empty_report(self):
        report = generate_discovery_report([])
        self.assertIn('0/5', report)
        self.assertIn('No', report)

    def test_report_shows_progress(self):
        convs = [_make_conversation(contact=f'C{i}', date=f'2026-06-{i:02d}') for i in range(1, 4)]
        report = generate_discovery_report(convs)
        self.assertIn('3/5', report)
        self.assertIn('No', report)  # not ready to lock

    def test_report_shows_ready_to_lock(self):
        convs = [_make_conversation(contact=f'C{i}', date=f'2026-06-{i:02d}') for i in range(1, 6)]
        report = generate_discovery_report(convs)
        self.assertIn('5/5', report)
        self.assertIn('Yes', report)

    def test_report_contains_icp_language_bank(self):
        c = _make_conversation(icp_language=['we just accept the rework'])
        report = generate_discovery_report([c])
        self.assertIn('ICP Language Bank', report)
        self.assertIn('we just accept the rework', report)

    def test_report_contains_copq_estimate(self):
        c = _make_conversation(copq_estimate=350000.0)
        report = generate_discovery_report([c])
        self.assertIn('£350,000.00', report)

    def test_report_contains_contact_name(self):
        c = _make_conversation(contact='Elena Rodriguez')
        report = generate_discovery_report([c])
        self.assertIn('Elena Rodriguez', report)

    def test_report_d1_defect_shown(self):
        c = DiscoveryConversation(
            contact_name='David Lee', date='2026-06-01',
            situation='x', complication='y', question='z', htdq='w',
        )
        report = generate_discovery_report([c])
        self.assertIn('D1', report)

    def test_report_scq_fields_shown(self):
        c = _make_conversation(
            situation='Plant at 65% OEE',
            complication='No measurement system',
            question='Where is the hidden factory?',
            htdq='How do we quantify it?',
        )
        report = generate_discovery_report([c])
        self.assertIn('Plant at 65% OEE', report)
        self.assertIn('No measurement system', report)


class TestDragonPhrase(unittest.TestCase):

    def test_dragon_stored(self):
        c = _make_conversation(dragon='we just accept the rework as part of the job')
        self.assertTrue(c.has_dragon())
        self.assertEqual(c.dragon, 'we just accept the rework as part of the job')

    def test_dragon_optional(self):
        c = _make_conversation()
        self.assertFalse(c.has_dragon())

    def test_d4_flagged_when_no_dragon(self):
        c = _make_conversation()
        r = check_readiness([c])
        self.assertIn('James Okafor', r['d4_contacts'])

    def test_d4_cleared_when_dragon_present(self):
        c = _make_conversation(dragon='nobody can see where the money is going')
        r = check_readiness([c])
        self.assertNotIn('James Okafor', r['d4_contacts'])

    def test_dragon_phrases_collected_in_readiness(self):
        c1 = _make_conversation(dragon='we just accept the rework')
        c2 = _make_conversation(contact='Sarah', date='2026-06-02', dragon='the costs are invisible to us')
        r = check_readiness([c1, c2])
        self.assertEqual(len(r['dragon_phrases']), 2)
        self.assertIn('we just accept the rework', r['dragon_phrases'])

    def test_dragon_phrases_not_collected_when_absent(self):
        c = _make_conversation()
        r = check_readiness([c])
        self.assertEqual(r['dragon_phrases'], [])

    def test_report_shows_dragon_section(self):
        c = _make_conversation(dragon='nobody can see where the rework costs go')
        report = generate_discovery_report([c])
        self.assertIn('Dragon Phrases', report)
        self.assertIn('nobody can see where the rework costs go', report)

    def test_report_shows_d4_defect(self):
        c = _make_conversation()
        report = generate_discovery_report([c])
        self.assertIn('D4', report)

    def test_report_dragon_verbatim_in_per_conversation(self):
        c = _make_conversation(dragon='the defects are just part of how we operate')
        report = generate_discovery_report([c])
        self.assertIn('Dragon (verbatim)', report)
        self.assertIn('the defects are just part of how we operate', report)

    def test_htdq_label_updated_in_report(self):
        c = _make_conversation()
        report = generate_discovery_report([c])
        self.assertIn('Hero/Treasure/Dragon/Quest', report)


class TestDiscoveryGenerator(unittest.TestCase):

    def test_log_conversation_wrapper(self):
        c = log_conversation(
            contact_name='James Okafor',
            date='2026-06-01',
            situation='OEE at 65%',
            complication='No measurement system',
            question='Where is the waste?',
            htdq=_HTDQ_EXAMPLE,
            dragon='we just accept the losses as normal',
            icp_language=['we just accept the rework'],
        )
        self.assertEqual(c.contact_name, 'James Okafor')
        self.assertTrue(c.has_icp_language())
        self.assertTrue(c.has_dragon())

    def test_log_conversation_wrapper_no_dragon(self):
        c = log_conversation(
            contact_name='Sarah Chen',
            date='2026-06-02',
            situation='x', complication='y', question='z', htdq='w',
        )
        self.assertFalse(c.has_dragon())

    def test_get_discovery_report_wrapper(self):
        convs = [_make_conversation()]
        report = get_discovery_report(convs)
        self.assertIn('SCQ Discovery Report', report)


if __name__ == '__main__':
    unittest.main()
