import unittest
from src.pillar3.proposal_builder import (
    calculate_rpn,
    classify_rpn,
    build_fmea,
    build_control_plan,
    calculate_romi,
    build_proposal,
    RPN_ACTION_THRESHOLD,
    RPN_ANDON_THRESHOLD,
    ROMI_MIN_ACCEPTABLE,
)


class TestRPN(unittest.TestCase):
    def test_calculate_rpn(self):
        self.assertEqual(calculate_rpn(8, 6, 4), 192)
        self.assertEqual(calculate_rpn(9, 5, 2), 90)
        self.assertEqual(calculate_rpn(10, 10, 10), 1000)

    def test_classify_rpn(self):
        self.assertEqual(classify_rpn(100), 'ACCEPT')
        self.assertEqual(classify_rpn(150), 'ACTION')
        self.assertEqual(classify_rpn(299), 'ACTION')
        self.assertEqual(classify_rpn(300), 'ANDON')
        self.assertEqual(classify_rpn(999), 'ANDON')


class TestFMEA(unittest.TestCase):
    def test_build_fmea(self):
        failure_modes = [
            {'mode': 'A', 'severity': 8, 'occurrence': 6, 'detection': 4},
            {'mode': 'B', 'severity': 9, 'occurrence': 5, 'detection': 2},
            {'mode': 'C', 'severity': 7, 'occurrence': 4, 'detection': 3},
        ]
        results = build_fmea(failure_modes)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['rpn'], 192)
        self.assertEqual(results[0]['classification'], 'ACTION')
        self.assertIn('Mitigate', results[0]['action'])

    def test_build_control_plan(self):
        failure_modes = [
            {'mode': 'A', 'severity': 8, 'occurrence': 6, 'detection': 4},  # RPN 192 → ACTION
            {'mode': 'B', 'severity': 9, 'occurrence': 5, 'detection': 2},  # RPN 90  → ACCEPT
        ]
        fmea = build_fmea(failure_modes)
        plan = build_control_plan(fmea)
        self.assertEqual(len(plan), 1)
        self.assertEqual(plan[0]['process_step'], 'A')


class TestROMI(unittest.TestCase):
    def test_calculate_romi_positive(self):
        romi = calculate_romi(2800000, 150000)
        self.assertAlmostEqual(romi, 17.6667, places=4)

    def test_calculate_romi_zero_cost(self):
        romi = calculate_romi(1000000, 0)
        self.assertIsNone(romi)

    def test_calculate_romi_negative(self):
        romi = calculate_romi(100000, 200000)
        self.assertEqual(romi, -0.5)


class TestProposalBuilder(unittest.TestCase):
    def setUp(self):
        self.agent2 = {
            'client_name': 'Test Client',
            'date': '2026-06-16',
            'copq_total': 14000000,
            'copq_table': [],
            'business_case_pass': True,
        }
        self.pricing = {
            'monthly_fee': 25000,
            'annual_fee': 150000,
            'fee_basis': '15% of CoPQ',
        }
        self.failure_modes = [
            {'mode': 'A', 'severity': 8, 'occurrence': 6, 'detection': 4},
            {'mode': 'B', 'severity': 9, 'occurrence': 5, 'detection': 2},
            {'mode': 'C', 'severity': 7, 'occurrence': 4, 'detection': 3},
        ]
        self.engagement_cost = 150000

    def test_build_proposal_success(self):
        # Default recovery_rate=0.20 → expected_benefit = 14M × 0.20 = £2,800,000
        proposal = build_proposal(
            self.agent2,
            self.pricing,
            self.failure_modes,
            self.engagement_cost,
        )
        self.assertIn('£14,000,000', proposal)
        self.assertIn('£150,000/year', proposal)
        self.assertIn('ROMI: 1766.7%', proposal)

    def test_missing_copq(self):
        del self.agent2['copq_total']
        with self.assertRaises(ValueError) as ctx:
            build_proposal(self.agent2, self.pricing, self.failure_modes, self.engagement_cost)
        self.assertIn('CoPQ total missing', str(ctx.exception))

    def test_missing_fee(self):
        del self.pricing['annual_fee']
        with self.assertRaises(ValueError) as ctx:
            build_proposal(self.agent2, self.pricing, self.failure_modes, self.engagement_cost)
        self.assertIn('Annual fee missing', str(ctx.exception))

    def test_business_case_failed(self):
        self.agent2['business_case_pass'] = False
        with self.assertRaises(ValueError) as ctx:
            build_proposal(self.agent2, self.pricing, self.failure_modes, self.engagement_cost)
        self.assertIn('Business case failed', str(ctx.exception))

    def test_too_few_failure_modes(self):
        with self.assertRaises(ValueError) as ctx:
            build_proposal(self.agent2, self.pricing, [], self.engagement_cost)
        self.assertIn('At least 3 failure modes', str(ctx.exception))

    def test_andon_block(self):
        bad_modes = self.failure_modes + [{'mode': 'D', 'severity': 10, 'occurrence': 10, 'detection': 10}]
        with self.assertRaises(ValueError) as ctx:
            build_proposal(self.agent2, self.pricing, bad_modes, self.engagement_cost)
        self.assertIn('ANDON', str(ctx.exception))

    def test_benefit_exceeds_copq(self):
        # Explicit override that exceeds copq_total should be rejected
        with self.assertRaises(ValueError) as ctx:
            build_proposal(
                self.agent2, self.pricing, self.failure_modes, self.engagement_cost,
                expected_benefit=15000000,
            )
        self.assertIn('cannot exceed CoPQ total', str(ctx.exception))

    def test_custom_recovery_rate(self):
        # 10% recovery on £14M = £1,400,000 benefit; ROMI = (1.4M - 0.15M) / 0.15M ≈ 8.333
        proposal = build_proposal(
            self.agent2, self.pricing, self.failure_modes, self.engagement_cost,
            recovery_rate=0.10,
        )
        self.assertIn('£1,400,000', proposal)

    def test_romi_warning(self):
        # Explicit benefit override: low ROMI should still generate proposal with warning
        proposal = build_proposal(
            self.agent2,
            self.pricing,
            self.failure_modes,
            engagement_cost=5000000,
            expected_benefit=100000,
        )
        self.assertIn('ROMI: -98.0%', proposal)
        self.assertIn('ROMI below 50%', proposal)


if __name__ == "__main__":
    unittest.main()
