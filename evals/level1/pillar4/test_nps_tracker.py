import unittest
from src.pillar4.nps_tracker import (
    NPSRecord,
    classify_nps,
    compute_nps_summary,
    generate_nps_debrief,
    is_debrief_required,
    get_open_debriefs,
)


class TestNPSRecord(unittest.TestCase):

    def test_g1_missing_engagement_raises(self):
        with self.assertRaises(ValueError) as ctx:
            NPSRecord(engagement_name='', client_name='Client', score=9)
        self.assertIn('engagement and client names', str(ctx.exception))

    def test_g3_invalid_score_raises(self):
        with self.assertRaises(ValueError) as ctx:
            NPSRecord(engagement_name='E', client_name='C', score=11)
        self.assertIn('score must be between 0 and 10', str(ctx.exception))

    def test_valid_record(self):
        rec = NPSRecord(engagement_name='E', client_name='C', score=9)
        self.assertEqual(rec.score, 9)
        self.assertIsNotNone(rec.date)


class TestClassifyNPS(unittest.TestCase):

    def test_promoter(self):
        self.assertEqual(classify_nps(9), 'Promoter')
        self.assertEqual(classify_nps(10), 'Promoter')

    def test_passive(self):
        self.assertEqual(classify_nps(7), 'Passive')
        self.assertEqual(classify_nps(8), 'Passive')

    def test_detractor(self):
        self.assertEqual(classify_nps(0), 'Detractor')
        self.assertEqual(classify_nps(6), 'Detractor')


class TestDebriefRequired(unittest.TestCase):

    def test_is_debrief_required(self):
        self.assertTrue(is_debrief_required(NPSRecord('E', 'C', 8)))
        self.assertTrue(is_debrief_required(NPSRecord('E', 'C', 6)))
        self.assertFalse(is_debrief_required(NPSRecord('E', 'C', 9)))
        self.assertFalse(is_debrief_required(NPSRecord('E', 'C', 10)))


class TestOpenDebriefs(unittest.TestCase):

    def test_get_open_debriefs(self):
        records = [
            NPSRecord('E1', 'C1', 9, debrief_conducted=False),   # Promoter, no debrief needed
            NPSRecord('E2', 'C2', 8, debrief_conducted=False),   # Passive, debrief needed
            NPSRecord('E3', 'C3', 6, debrief_conducted=True),    # Detractor, debrief done
            NPSRecord('E4', 'C4', 7, debrief_conducted=False),   # Passive, debrief needed
        ]
        open_list = get_open_debriefs(records)
        self.assertEqual(len(open_list), 2)
        self.assertEqual(open_list[0].engagement_name, 'E2')
        self.assertEqual(open_list[1].engagement_name, 'E4')


class TestComputeNPSSummary(unittest.TestCase):

    def test_empty_records(self):
        summary = compute_nps_summary([])
        self.assertEqual(summary['total'], 0)
        self.assertEqual(summary['threshold_status'], 'NO_DATA')

    def test_all_promoters(self):
        records = [
            NPSRecord('E1', 'C1', 10),
            NPSRecord('E2', 'C2', 9),
        ]
        summary = compute_nps_summary(records)
        self.assertEqual(summary['nps'], 100.0)
        self.assertEqual(summary['threshold_status'], 'PASS')
        self.assertFalse(summary['debrief_needed'])

    def test_mixed(self):
        records = [
            NPSRecord('E1', 'C1', 10),  # Promoter
            NPSRecord('E2', 'C2', 7),   # Passive
            NPSRecord('E3', 'C3', 5),   # Detractor
        ]
        summary = compute_nps_summary(records)
        self.assertEqual(summary['promoters'], 1)
        self.assertEqual(summary['passives'], 1)
        self.assertEqual(summary['detractors'], 1)
        self.assertEqual(summary['nps'], 0.0)
        self.assertEqual(summary['threshold_status'], 'ANDON')
        self.assertTrue(summary['debrief_needed'])

    def test_andon_threshold(self):
        # 7 promoters, 2 passives, 1 detractor => NPS = 60 -> PASS
        records1 = [
            NPSRecord(f'E{i}', f'C{i}', 9) for i in range(7)
        ] + [
            NPSRecord(f'E{i}', f'C{i}', 7) for i in range(2)
        ] + [
            NPSRecord('E9', 'C9', 6)
        ]
        summary1 = compute_nps_summary(records1)
        self.assertEqual(summary1['nps'], 60.0)
        self.assertEqual(summary1['threshold_status'], 'PASS')

        # 6 promoters, 2 passives, 2 detractors => NPS = 40 -> ANDON
        records2 = [
            NPSRecord(f'E{i}', f'C{i}', 9) for i in range(6)
        ] + [
            NPSRecord(f'E{i}', f'C{i}', 7) for i in range(2)
        ] + [
            NPSRecord(f'E{i}', f'C{i}', 5) for i in range(2)
        ]
        summary2 = compute_nps_summary(records2)
        self.assertEqual(summary2['nps'], 40.0)
        self.assertEqual(summary2['threshold_status'], 'ANDON')
        self.assertTrue(summary2['debrief_needed'])


class TestGenerateDebrief(unittest.TestCase):

    def test_debrief_includes_score(self):
        record = NPSRecord('E', 'C', 3)
        debrief = generate_nps_debrief(record)
        self.assertIn('3/10', debrief)
        self.assertIn('What made you score us 3/10?', debrief)


if __name__ == "__main__":
    unittest.main()
