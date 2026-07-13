import unittest
from src.pillar4.ftar_tracker import FTARRecord, compute_ftar_summary, threshold_status

class TestFTARRecord(unittest.TestCase):

    def test_g1_missing_name_raises(self):
        with self.assertRaises(ValueError) as ctx:
            FTARRecord(deliverable_name='', status='PASS')
        self.assertIn('G1', str(ctx.exception))

    def test_g2_invalid_status_raises(self):
        with self.assertRaises(ValueError) as ctx:
            FTARRecord(deliverable_name='Report', status='MAYBE')
        self.assertIn('G2', str(ctx.exception))

    def test_valid_record(self):
        rec = FTARRecord(deliverable_name='Report', status='PASS')
        self.assertEqual(rec.deliverable_name, 'Report')
        self.assertIsNotNone(rec.submission_date)


class TestComputeFTARSummary(unittest.TestCase):

    def test_empty_records(self):
        summary = compute_ftar_summary([])
        self.assertEqual(summary.total, 0)
        self.assertEqual(summary.threshold_status, 'NO_DATA')

    def test_all_pass(self):
        records = [FTARRecord('A', 'PASS'), FTARRecord('B', 'PASS')]
        summary = compute_ftar_summary(records)
        self.assertEqual(summary.ftar, 1.0)
        self.assertEqual(summary.threshold_status, 'PASS')

    def test_andon(self):
        records = [FTARRecord('A', 'FAIL'), FTARRecord('B', 'FAIL')]
        summary = compute_ftar_summary(records)
        self.assertEqual(summary.ftar, 0.0)
        self.assertEqual(summary.threshold_status, 'ANDON')

    def test_warning(self):
        records = [FTARRecord(f'D{i}', 'PASS') for i in range(8)]
        records.append(FTARRecord('D9', 'FAIL'))
        summary = compute_ftar_summary(records)
        self.assertAlmostEqual(summary.ftar, 8/9, places=3)
        self.assertEqual(summary.threshold_status, 'WARNING')

    def test_failure_reasons(self):
        rec1 = FTARRecord('A', 'FAIL', failure_reason='Wrong format')
        rec2 = FTARRecord('B', 'PASS')
        summary = compute_ftar_summary([rec1, rec2])
        self.assertIn('Wrong format', summary.failure_reasons)


class TestThresholdStatus(unittest.TestCase):

    def test_no_data(self):
        self.assertEqual(threshold_status(0.0, 0), 'NO_DATA')

    def test_pass(self):
        self.assertEqual(threshold_status(0.92, 10), 'PASS')

    def test_warning(self):
        self.assertEqual(threshold_status(0.87, 10), 'WARNING')

    def test_andon(self):
        self.assertEqual(threshold_status(0.80, 10), 'ANDON')

if __name__ == "__main__":
    unittest.main()
