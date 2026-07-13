import unittest
from src.pillar4.control_plan_generator import generate_control_plan, _format_spec

class TestControlPlanGenerator(unittest.TestCase):

    def test_generate_basic(self):
        ctq = [{'name': 'CoPQ Reduction', 'lsl': 20, 'usl': None}]
        cp = generate_control_plan(ctq, client_name='Test', engagement_name='Test', date='2026-06-17')
        self.assertIn('CoPQ Reduction', cp)
        self.assertIn('≥ 20', cp)
        self.assertIn('Test / Test', cp)

    def test_missing_ctq_raises(self):
        with self.assertRaises(ValueError) as ctx:
            generate_control_plan([])
        self.assertIn('No CTQ nodes', str(ctx.exception))

    def test_format_spec(self):
        self.assertEqual(_format_spec(20, 30), '20 – 30')
        self.assertEqual(_format_spec(20, None), '≥ 20')
        self.assertEqual(_format_spec(None, 30), '≤ 30')
        self.assertEqual(_format_spec(None, None), 'Not specified')

    def test_fmea_and_andon(self):
        ctq = [{'name': 'Critical CTQ', 'lsl': 0, 'usl': 10}]
        fmea = [{'mode': 'Critical CTQ', 'rpn': 350, 'classification': 'ANDON', 'action': 'Stop and redesign'}]
        cp = generate_control_plan(ctq, fmea_results=fmea)
        self.assertIn('ANDON', cp)
        self.assertIn('Stop and redesign', cp)

    def test_process_step_mapping(self):
        ctq = [{'name': 'Assembly Yield', 'lsl': 95, 'usl': 100}]
        steps = ['Incoming Inspection', 'Assembly', 'Test']
        cp = generate_control_plan(ctq, process_steps=steps)
        self.assertIn('Assembly', cp)  # Mapping should pick Assembly

    def test_optional_columns(self):
        ctq = [{'name': 'Yield', 'lsl': 95, 'usl': 100}]
        cp = generate_control_plan(ctq, include_owner=False, include_sample_size=False, include_reaction_plan=False)
        self.assertNotIn('Owner', cp)
        self.assertNotIn('Sample Size', cp)
        self.assertNotIn('Reaction Plan', cp)

if __name__ == "__main__":
    unittest.main()
