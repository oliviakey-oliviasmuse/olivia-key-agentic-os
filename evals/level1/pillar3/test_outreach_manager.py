import unittest
from datetime import datetime, timedelta
from src.pillar3.outreach_manager import (
    suggest_action,
    generate_script,
    track_ltv_cac,
    FOLLOWUP_DAYS,
    REMINDER_GRACE,
    LTV_CAC_RATIO_MIN,
    LTV_CAC_RATIO_GOOD,
    SCRIPTS,
)


class TestSuggestAction(unittest.TestCase):
    def test_new_lead_no_interaction_not_overdue(self):
        """No prior interaction → not overdue, but action is still needed."""
        result = suggest_action('Prospect A', stage='New Lead', current_date='2026-06-16')
        self.assertEqual(result['action'], 'Send cold DM')
        self.assertEqual(result['script'], SCRIPTS['cold_dm'])
        self.assertFalse(result['overdue'])

    def test_new_lead_followup_needed_not_overdue(self):
        """6 days after last interaction → action needed, not yet overdue."""
        last_date = (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d')
        result = suggest_action('Prospect A', last_interaction=last_date, stage='New Lead')
        self.assertEqual(result['action'], 'Send cold DM')
        self.assertFalse(result['overdue'])

    def test_new_lead_overdue(self):
        """8+ days after last interaction → action needed AND overdue."""
        last_date = (datetime.now() - timedelta(days=8)).strftime('%Y-%m-%d')
        result = suggest_action('Prospect A', last_interaction=last_date, stage='New Lead')
        self.assertEqual(result['action'], 'Send cold DM')
        self.assertTrue(result['overdue'])

    def test_engaged_followup(self):
        last_date = (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d')
        result = suggest_action('Prospect B', last_interaction=last_date, stage='Engaged')
        self.assertEqual(result['action'], 'Send value-add follow-up')
        self.assertEqual(result['script'], SCRIPTS['value_add'])

    def test_proposal_sent_checkin(self):
        last_date = (datetime.now() - timedelta(days=8)).strftime('%Y-%m-%d')
        result = suggest_action('Prospect C', last_interaction=last_date, stage='Proposal Sent')
        self.assertEqual(result['action'], 'Send check-in')
        self.assertEqual(result['script'], SCRIPTS['check_in'])

    def test_client_quarterly(self):
        last_date = (datetime.now() - timedelta(days=95)).strftime('%Y-%m-%d')
        result = suggest_action('Client X', last_interaction=last_date, stage='Client')
        self.assertEqual(result['action'], 'Send referral request')
        self.assertEqual(result['script'], SCRIPTS['referral'])

    def test_client_not_due(self):
        last_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        result = suggest_action('Client X', last_interaction=last_date, stage='Client')
        self.assertEqual(result['action'], 'No action needed (client engaged)')
        self.assertIsNone(result['script'])

    def test_returns_days_since(self):
        last_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        result = suggest_action('Prospect A', last_interaction=last_date, stage='New Lead')
        self.assertEqual(result['days_since'], 3)

    def test_lost_stage_no_action(self):
        result = suggest_action('Lost Prospect', stage='Lost')
        self.assertEqual(result['action'], 'No action needed – prospect lost')
        self.assertIsNone(result['script'])
        self.assertFalse(result['overdue'])

    def test_no_action_does_not_set_recommended_date(self):
        last_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        result = suggest_action('Client X', last_interaction=last_date, stage='Client')
        self.assertIsNone(result['recommended_date'])

    def test_new_lead_no_interaction_sets_recommended_date(self):
        result = suggest_action('Prospect A', stage='New Lead', current_date='2026-06-16')
        self.assertIsNotNone(result['recommended_date'])
        expected = (datetime.strptime('2026-06-16', '%Y-%m-%d') + timedelta(days=FOLLOWUP_DAYS)).strftime('%Y-%m-%d')
        self.assertEqual(result['recommended_date'], expected)


class TestGenerateScript(unittest.TestCase):
    def test_generate_cold_dm(self):
        context = {'name': 'Sarah', 'industry': 'Aerospace', 'pain': 'hidden factory'}
        script = generate_script('Sarah', context, 'cold_dm')
        self.assertIn('Sarah', script)
        self.assertIn('Aerospace', script)
        self.assertIn('hidden factory', script)

    def test_generate_follow_up(self):
        context = {'name': 'John', 'industry': 'Logistics', 'pain': 'rework'}
        script = generate_script('John', context, 'follow_up')
        self.assertIn('John', script)
        self.assertIn('rework', script)

    def test_generate_value_add(self):
        context = {'name': 'Emma', 'industry': 'Manufacturing', 'topic': 'CoPQ reduction'}
        script = generate_script('Emma', context, 'value_add')
        self.assertIn('Emma', script)
        self.assertIn('CoPQ reduction', script)

    def test_generate_uses_default(self):
        context = {'name': 'Alex'}
        script = generate_script('Alex', context, 'unknown_script')
        self.assertIn('Alex', script)


class TestLTV_CAC(unittest.TestCase):
    def test_ltv_cac_healthy(self):
        result = track_ltv_cac(cac=1000, ltv=6000)
        self.assertEqual(result['ratio'], 6.0)
        self.assertEqual(result['status'], 'HEALTHY')

    def test_ltv_cac_acceptable(self):
        result = track_ltv_cac(cac=1000, ltv=3500)
        self.assertEqual(result['ratio'], 3.5)
        self.assertEqual(result['status'], 'ACCEPTABLE')

    def test_ltv_cac_warning(self):
        result = track_ltv_cac(cac=1000, ltv=2000)
        self.assertEqual(result['ratio'], 2.0)
        self.assertEqual(result['status'], 'WARNING')

    def test_ltv_cac_zero_cac(self):
        result = track_ltv_cac(cac=0, ltv=5000)
        self.assertEqual(result['status'], 'ERROR')


if __name__ == "__main__":
    unittest.main()
