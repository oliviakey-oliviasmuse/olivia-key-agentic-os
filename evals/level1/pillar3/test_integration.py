import unittest
from unittest.mock import patch, Mock
from src.pillar3.integration import build_proposal_with_pricing


class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.agent2_output = {
            'copq_total': 14_000_000,
            'copq_table': [],
            'business_case_pass': True,
            'client_name': 'Test Client',
            'date': '2026-06-16',
        }
        self.failure_modes = [
            {'mode': 'A', 'severity': 8, 'occurrence': 6, 'detection': 4},
            {'mode': 'B', 'severity': 9, 'occurrence': 5, 'detection': 2},
            {'mode': 'C', 'severity': 7, 'occurrence': 4, 'detection': 3},
        ]

    @patch('src.pillar3.proposal_builder.build_proposal')
    def test_build_proposal_with_pricing(self, mock_build_proposal):
        mock_calculate_fee = Mock(return_value={
            'monthly_fee': 25_000,
            'annual_fee': 300_000,
            'fee_basis': '15% of CoPQ recovery',
        })
        mock_build_proposal.return_value = 'Proposal markdown'

        result = build_proposal_with_pricing(
            self.agent2_output,
            self.failure_modes,
            fee_percentage=0.15,
            recovery_rate=0.20,
            floor=5000,
            calculate_fee_fn=mock_calculate_fee,
        )

        mock_calculate_fee.assert_called_once_with(
            copq_total=14_000_000,
            fee_percentage=0.15,
            floor=5000,
        )

        mock_build_proposal.assert_called_once()
        _, kwargs = mock_build_proposal.call_args
        self.assertEqual(kwargs['agent2_output'], self.agent2_output)
        self.assertEqual(kwargs['pricing'], mock_calculate_fee.return_value)
        self.assertEqual(kwargs['engagement_cost'], 300_000)
        self.assertEqual(kwargs['expected_benefit'], 2_800_000)  # 14M × 0.20

        self.assertEqual(result, 'Proposal markdown')

    def test_build_proposal_with_pricing_missing_copq(self):
        del self.agent2_output['copq_total']
        with self.assertRaises(ValueError) as ctx:
            build_proposal_with_pricing(self.agent2_output, self.failure_modes)
        self.assertIn('CoPQ total missing', str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
