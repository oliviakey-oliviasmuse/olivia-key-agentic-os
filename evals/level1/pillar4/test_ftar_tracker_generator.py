import unittest
from src.pillar4.ftar_tracker import FTARRecord
from src.pillar4.ftar_tracker_generator import add_record, generate_ftar_report


class TestAddRecord(unittest.TestCase):

    def test_add_record_returns_ftar_record(self):
        rec = add_record('Report', 'PASS')
        self.assertIsInstance(rec, FTARRecord)
        self.assertEqual(rec.deliverable_name, 'Report')

    def test_add_record_g1_raises(self):
        with self.assertRaises(ValueError):
            add_record('', 'PASS')


class TestGenerateFTARReport(unittest.TestCase):

    def test_report_contains_ftar(self):
        records = [
            add_record('Report A', 'PASS'),
            add_record('Report B', 'FAIL', failure_reason='Wrong format'),
        ]
        md = generate_ftar_report(records)
        self.assertIn('FTAR Report', md)
        self.assertIn('ANDON', md)  # 1/2 = 50%, below 85%
        self.assertIn('Wrong format', md)

    def test_report_pass_status(self):
        records = [add_record(f'D{i}', 'PASS') for i in range(10)]
        md = generate_ftar_report(records)
        self.assertIn('PASS', md)
        self.assertIn('100.0%', md)

    def test_report_no_data(self):
        md = generate_ftar_report([])
        self.assertIn('NO_DATA', md)

if __name__ == "__main__":
    unittest.main()
