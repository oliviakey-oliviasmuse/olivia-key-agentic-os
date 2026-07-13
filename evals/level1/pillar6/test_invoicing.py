import unittest
from datetime import datetime, timedelta
from src.pillar6.invoicing import Invoice, compute_summary, generate_invoice_report, generate_summary_report


TODAY = datetime.now().strftime('%Y-%m-%d')


def _days_ago(n: int) -> str:
    return (datetime.now() - timedelta(days=n)).strftime('%Y-%m-%d')


class TestInvoiceCreation(unittest.TestCase):
    def test_valid_invoice_defaults(self):
        inv = Invoice(client_name='Acme', engagement_name='Project X', invoice_date='2026-06-25', amount=5000.0)
        self.assertEqual(inv.client_name, 'Acme')
        self.assertEqual(inv.amount, 5000.0)
        self.assertEqual(inv.payment_terms_days, 14)
        self.assertEqual(inv.currency, 'GBP')
        self.assertIn(inv.status, ('pending', 'overdue'))

    def test_invoice_today_is_pending(self):
        inv = Invoice(client_name='Acme', engagement_name='Project X', invoice_date=TODAY, amount=5000.0)
        self.assertEqual(inv.status, 'pending')

    def test_invoice_with_paid_date_is_paid(self):
        inv = Invoice(
            client_name='Acme', engagement_name='Project X',
            invoice_date='2026-06-01', amount=5000.0,
            paid_date='2026-06-10',
        )
        self.assertEqual(inv.status, 'paid')

    def test_overdue_invoice(self):
        inv = Invoice(client_name='Acme', engagement_name='Project', invoice_date=_days_ago(20), amount=5000.0)
        self.assertEqual(inv.status, 'overdue')


class TestGateEnforcement(unittest.TestCase):
    def test_g1_missing_client(self):
        with self.assertRaises(ValueError) as ctx:
            Invoice(client_name='', engagement_name='Project', invoice_date='2026-06-25', amount=5000)
        self.assertIn('G1', str(ctx.exception))

    def test_g2_missing_engagement(self):
        with self.assertRaises(ValueError) as ctx:
            Invoice(client_name='Acme', engagement_name='', invoice_date='2026-06-25', amount=5000)
        self.assertIn('G2', str(ctx.exception))

    def test_g3_invalid_date(self):
        with self.assertRaises(ValueError) as ctx:
            Invoice(client_name='Acme', engagement_name='Project', invoice_date='2026-99-99', amount=5000)
        self.assertIn('G3', str(ctx.exception))

    def test_g3_malformed_date_string(self):
        with self.assertRaises(ValueError) as ctx:
            Invoice(client_name='Acme', engagement_name='Project', invoice_date='not-a-date', amount=5000)
        self.assertIn('G3', str(ctx.exception))

    def test_g4_amount_zero(self):
        with self.assertRaises(ValueError) as ctx:
            Invoice(client_name='Acme', engagement_name='Project', invoice_date='2026-06-25', amount=0)
        self.assertIn('G4', str(ctx.exception))

    def test_g4_amount_negative(self):
        with self.assertRaises(ValueError) as ctx:
            Invoice(client_name='Acme', engagement_name='Project', invoice_date='2026-06-25', amount=-100)
        self.assertIn('G4', str(ctx.exception))

    def test_paid_date_invalid_format(self):
        with self.assertRaises(ValueError):
            Invoice(client_name='Acme', engagement_name='Project', invoice_date='2026-06-25', amount=5000, paid_date='invalid')


class TestDueDateAndDebtorDays(unittest.TestCase):
    def test_due_date_net14(self):
        inv = Invoice(client_name='Acme', engagement_name='Project', invoice_date='2026-06-25', amount=5000)
        self.assertEqual(inv.due_date(), '2026-07-09')

    def test_due_date_custom_terms(self):
        inv = Invoice(client_name='Acme', engagement_name='Project', invoice_date='2026-06-01', amount=5000, payment_terms_days=30)
        self.assertEqual(inv.due_date(), '2026-07-01')

    def test_debtor_days_pending_is_int(self):
        inv = Invoice(client_name='Acme', engagement_name='Project', invoice_date=TODAY, amount=5000)
        self.assertIsInstance(inv.debtor_days(), int)

    def test_debtor_days_pending_today_is_zero(self):
        inv = Invoice(client_name='Acme', engagement_name='Project', invoice_date=TODAY, amount=5000)
        self.assertEqual(inv.debtor_days(), 0)

    def test_debtor_days_paid(self):
        inv = Invoice(
            client_name='Acme', engagement_name='Project',
            invoice_date='2026-06-01', amount=5000,
            paid_date='2026-06-10',
        )
        self.assertEqual(inv.debtor_days(), 9)

    def test_debtor_days_overdue(self):
        inv = Invoice(client_name='Acme', engagement_name='Project', invoice_date=_days_ago(20), amount=5000)
        self.assertEqual(inv.debtor_days(), 20)


class TestChasingProtocol(unittest.TestCase):
    def test_no_action_within_21_days(self):
        inv = Invoice(client_name='Acme', engagement_name='Project', invoice_date=_days_ago(10), amount=5000)
        self.assertEqual(inv.chasing_action(), 'None')

    def test_email_at_day_22(self):
        inv = Invoice(client_name='Acme', engagement_name='Project', invoice_date=_days_ago(22), amount=5000)
        self.assertEqual(inv.chasing_action(), 'Email Day 21')

    def test_call_at_day_26(self):
        inv = Invoice(client_name='Acme', engagement_name='Project', invoice_date=_days_ago(26), amount=5000)
        self.assertEqual(inv.chasing_action(), 'Call Day 25')

    def test_final_notice_at_day_31(self):
        inv = Invoice(client_name='Acme', engagement_name='Project', invoice_date=_days_ago(31), amount=5000)
        self.assertEqual(inv.chasing_action(), 'Final Notice Day 30')

    def test_chasing_action_paid_returns_paid(self):
        inv = Invoice(
            client_name='Acme', engagement_name='Project',
            invoice_date='2026-06-01', amount=5000,
            paid_date='2026-06-10',
        )
        self.assertEqual(inv.chasing_action(), 'Paid')

    def test_boundary_day_21_no_action(self):
        # exactly 21 days — NOT > 21, so still "None"
        inv = Invoice(client_name='Acme', engagement_name='Project', invoice_date=_days_ago(21), amount=5000)
        self.assertEqual(inv.chasing_action(), 'None')

    def test_boundary_day_25_no_call(self):
        # exactly 25 days — NOT > 25, so still "Email Day 21"
        inv = Invoice(client_name='Acme', engagement_name='Project', invoice_date=_days_ago(25), amount=5000)
        self.assertEqual(inv.chasing_action(), 'Email Day 21')

    def test_boundary_day_30_no_final_notice(self):
        # exactly 30 days — NOT > 30, so still "Call Day 25"
        inv = Invoice(client_name='Acme', engagement_name='Project', invoice_date=_days_ago(30), amount=5000)
        self.assertEqual(inv.chasing_action(), 'Call Day 25')


class TestComputeSummary(unittest.TestCase):
    def test_mixed_invoice_summary(self):
        inv1 = Invoice(client_name='Acme', engagement_name='Project', invoice_date='2026-06-01', amount=5000, paid_date='2026-06-10')
        inv2 = Invoice(client_name='Beta', engagement_name='Project', invoice_date='2026-06-01', amount=3000)
        summary = compute_summary([inv1, inv2])
        self.assertEqual(summary['total'], 2)
        self.assertEqual(summary['total_issued'], 8000.0)
        self.assertEqual(summary['total_paid'], 5000.0)
        self.assertEqual(summary['total_overdue'], 3000.0)

    def test_all_paid_avg_debtor_days_zero(self):
        inv = Invoice(client_name='Acme', engagement_name='Project', invoice_date='2026-06-01', amount=5000, paid_date='2026-06-10')
        summary = compute_summary([inv])
        self.assertEqual(summary['avg_debtor_days'], 0.0)

    def test_empty_list(self):
        summary = compute_summary([])
        self.assertEqual(summary['total'], 0)
        self.assertEqual(summary['total_issued'], 0.0)
        self.assertEqual(summary['avg_debtor_days'], 0.0)

    def test_avg_debtor_days_unpaid(self):
        inv1 = Invoice(client_name='Acme', engagement_name='P', invoice_date=_days_ago(10), amount=1000)
        inv2 = Invoice(client_name='Beta', engagement_name='P', invoice_date=_days_ago(20), amount=1000)
        summary = compute_summary([inv1, inv2])
        self.assertAlmostEqual(summary['avg_debtor_days'], 15.0)


class TestReportGeneration(unittest.TestCase):
    def test_invoice_report_contains_key_fields(self):
        # Use a recent date so status is 'pending' (within Net 14 terms).
        # Hardcoded past dates age out of the payment window.
        inv = Invoice(client_name='Acme', engagement_name='Project', invoice_date=_days_ago(5), amount=5000)
        report = generate_invoice_report(inv)
        self.assertIn('Acme', report)
        self.assertIn('£5,000.00', report)
        self.assertIn('pending', report)

    def test_invoice_report_currency_symbol_gbp(self):
        inv = Invoice(client_name='Acme', engagement_name='Project', invoice_date=TODAY, amount=1000, currency='GBP')
        report = generate_invoice_report(inv)
        self.assertIn('£1,000.00', report)
        self.assertNotIn('GBP 1,000.00', report)

    def test_invoice_report_overdue_status(self):
        inv = Invoice(client_name='Acme', engagement_name='Project', invoice_date=_days_ago(20), amount=2500)
        report = generate_invoice_report(inv)
        self.assertIn('overdue', report)

    def test_invoice_report_chasing_present(self):
        inv = Invoice(client_name='Acme', engagement_name='Project', invoice_date=_days_ago(22), amount=2500)
        report = generate_invoice_report(inv)
        self.assertIn('Email Day 21', report)

    def test_summary_report_totals(self):
        inv1 = Invoice(client_name='Acme', engagement_name='Project', invoice_date='2026-06-01', amount=5000)
        inv2 = Invoice(client_name='Beta', engagement_name='Project', invoice_date='2026-06-01', amount=3000)
        report = generate_summary_report([inv1, inv2])
        self.assertIn('Total invoices: 2', report)
        self.assertIn('Total issued: 8,000.00', report)

    def test_summary_report_empty(self):
        report = generate_summary_report([])
        self.assertIn('Total invoices: 0', report)
        self.assertIn('Average debtor days: 0.0', report)


if __name__ == "__main__":
    unittest.main()
