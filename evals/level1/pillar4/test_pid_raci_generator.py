import unittest
from src.pillar4.pid_raci_generator import generate_pid_from_inputs

class TestPIDRACIGenerator(unittest.TestCase):

    def test_generate_basic(self):
        deliverables = [{'name': 'Report', 'responsible': 'Consultant', 'accountable': 'Client'}]
        pid_md = generate_pid_from_inputs(
            client='Acme',
            engagement='Project',
            scope='Reduce CoPQ',
            deliverables=deliverables,
            quality_standards=['CTQ 1'],
        )
        self.assertIn('Acme', pid_md)
        self.assertIn('Reduce CoPQ', pid_md)
        self.assertIn('Report', pid_md)
        self.assertIn('RACI Matrix', pid_md)

    def test_missing_role_warning(self):
        deliverables = [{'name': 'Report'}]
        pid_md = generate_pid_from_inputs(
            client='Acme',
            engagement='Project',
            scope='Scope',
            deliverables=deliverables,
            quality_standards=['Q'],
        )
        self.assertIn('Warning', pid_md)
        self.assertIn('No Responsible or Accountable', pid_md)

if __name__ == "__main__":
    unittest.main()
