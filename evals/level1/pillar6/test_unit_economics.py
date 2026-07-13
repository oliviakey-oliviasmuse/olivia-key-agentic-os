import unittest
from src.pillar6.unit_economics import (
    UnitEconomics,
    generate_unit_economics_report,
    generate_multi_channel_report,
)


def _ue(
    channel='LinkedIn',
    acquisition_cost=5000.0,
    new_customers=10,
    avg_monthly_margin=200.0,
    avg_engagement_duration=24.0,
    revenue_attributed=15000.0,
    period='quarter',
    date='2026-06-25',
):
    return UnitEconomics(
        channel=channel,
        acquisition_cost=acquisition_cost,
        new_customers=new_customers,
        avg_monthly_margin=avg_monthly_margin,
        avg_engagement_duration=avg_engagement_duration,
        revenue_attributed=revenue_attributed,
        period=period,
        date=date,
    )


class TestUnitEconomicsMetrics(unittest.TestCase):
    def test_cac(self):
        # 5000 / 10 = 500
        self.assertEqual(_ue().cac, 500.0)

    def test_clv(self):
        # 200 * 24 = 4800
        self.assertEqual(_ue().clv, 4800.0)

    def test_payback_months(self):
        # 500 / 200 = 2.5
        self.assertAlmostEqual(_ue().payback_months, 2.5)

    def test_romi_positive(self):
        # (15000 - 5000) / 5000 * 100 = 200%
        self.assertAlmostEqual(_ue().romi, 200.0)

    def test_romi_negative(self):
        # (15000 - 20000) / 20000 * 100 = -25%
        ue = _ue(acquisition_cost=20000, revenue_attributed=15000)
        self.assertAlmostEqual(ue.romi, -25.0)

    def test_cac_single_customer(self):
        ue = _ue(acquisition_cost=3000, new_customers=1)
        self.assertEqual(ue.cac, 3000.0)

    def test_clv_one_month_engagement(self):
        ue = _ue(avg_monthly_margin=500, avg_engagement_duration=1)
        self.assertEqual(ue.clv, 500.0)


class TestGateEnforcement(unittest.TestCase):
    def test_g1_missing_channel(self):
        with self.assertRaises(ValueError) as ctx:
            _ue(channel='')
        self.assertIn('G1', str(ctx.exception))

    def test_g2_zero_customers(self):
        with self.assertRaises(ValueError) as ctx:
            _ue(new_customers=0)
        self.assertIn('G2', str(ctx.exception))

    def test_g2_negative_customers(self):
        with self.assertRaises(ValueError) as ctx:
            _ue(new_customers=-5)
        self.assertIn('G2', str(ctx.exception))

    def test_g3_zero_margin(self):
        with self.assertRaises(ValueError) as ctx:
            _ue(avg_monthly_margin=0)
        self.assertIn('G3', str(ctx.exception))

    def test_g3_negative_margin(self):
        with self.assertRaises(ValueError) as ctx:
            _ue(avg_monthly_margin=-100)
        self.assertIn('G3', str(ctx.exception))

    def test_g4_zero_revenue(self):
        with self.assertRaises(ValueError) as ctx:
            _ue(revenue_attributed=0)
        self.assertIn('G4', str(ctx.exception))

    def test_g4_negative_revenue(self):
        with self.assertRaises(ValueError) as ctx:
            _ue(revenue_attributed=-1000)
        self.assertIn('G4', str(ctx.exception))

    def test_zero_acquisition_cost_rejected(self):
        with self.assertRaises(ValueError):
            _ue(acquisition_cost=0)


class TestStatusClassification(unittest.TestCase):
    def test_cac_vs_clv_ok(self):
        # CAC 500 < CLV 4800
        self.assertEqual(_ue().cac_vs_clv_status(), "OK")

    def test_cac_vs_clv_warning(self):
        # CAC = 5000/1 = 5000, CLV = 200*12 = 2400 → CAC > CLV → WARNING
        ue = _ue(new_customers=1, avg_engagement_duration=12)
        self.assertGreater(ue.cac, ue.clv)
        self.assertEqual(ue.cac_vs_clv_status(), "WARNING – CAC exceeds CLV")

    def test_cac_vs_clv_boundary_equal(self):
        # CAC == CLV → OK (not exceeds)
        ue = _ue(acquisition_cost=4800, new_customers=1, avg_monthly_margin=200, avg_engagement_duration=24)
        self.assertEqual(ue.cac, ue.clv)
        self.assertEqual(ue.cac_vs_clv_status(), "OK")

    def test_payback_ok(self):
        # payback = 500/200 = 2.5 months ≤ 12 → OK
        self.assertEqual(_ue().payback_status(), "OK")

    def test_payback_ok_boundary_at_12_months(self):
        # CAC = 1200, margin = 100 → payback = 12 → OK (not > 12)
        ue = _ue(acquisition_cost=1200, new_customers=1, avg_monthly_margin=100)
        self.assertAlmostEqual(ue.payback_months, 12.0)
        self.assertEqual(ue.payback_status(), "OK")

    def test_payback_warning(self):
        # CAC = 5000, margin = 100 → payback = 50 months → WARNING
        ue = _ue(acquisition_cost=5000, new_customers=1, avg_monthly_margin=100)
        self.assertGreater(ue.payback_months, 12)
        self.assertEqual(ue.payback_status(), "WARNING – payback > 12 months")

    def test_romi_ok(self):
        self.assertEqual(_ue().romi_status(), "OK")

    def test_romi_warning(self):
        ue = _ue(acquisition_cost=20000, revenue_attributed=15000)
        self.assertEqual(ue.romi_status(), "WARNING – negative ROMI")

    def test_romi_ok_at_zero_boundary(self):
        # revenue == cost → ROMI = 0% → OK (not < 0)
        ue = _ue(acquisition_cost=5000, revenue_attributed=5000)
        self.assertAlmostEqual(ue.romi, 0.0)
        self.assertEqual(ue.romi_status(), "OK")


class TestReportGeneration(unittest.TestCase):
    def test_report_contains_channel(self):
        report = generate_unit_economics_report(_ue())
        self.assertIn('LinkedIn', report)

    def test_report_contains_cac(self):
        report = generate_unit_economics_report(_ue())
        self.assertIn('CAC: £500.00', report)

    def test_report_contains_clv(self):
        report = generate_unit_economics_report(_ue())
        self.assertIn('CLV: £4,800.00', report)

    def test_report_contains_payback(self):
        report = generate_unit_economics_report(_ue())
        self.assertIn('Payback Period: 2.5 months', report)

    def test_report_contains_romi(self):
        report = generate_unit_economics_report(_ue())
        self.assertIn('ROMI: 200.0%', report)

    def test_report_contains_status_section(self):
        report = generate_unit_economics_report(_ue())
        self.assertIn('## Status', report)
        self.assertIn('CAC vs CLV: OK', report)
        self.assertIn('Payback: OK', report)
        self.assertIn('ROMI: OK', report)

    def test_report_warning_flags(self):
        # CAC = 5000, CLV = 200*1 = 200 → WARNING; ROMI negative
        ue = _ue(acquisition_cost=5000, new_customers=1, avg_engagement_duration=1, revenue_attributed=3000)
        report = generate_unit_economics_report(ue)
        self.assertIn('WARNING – CAC exceeds CLV', report)
        self.assertIn('WARNING – negative ROMI', report)

    def test_report_date_in_header(self):
        report = generate_unit_economics_report(_ue(date='2026-06-25'))
        self.assertIn('2026-06-25', report)


class TestMultiChannelReport(unittest.TestCase):
    def test_multi_channel_contains_all_channels(self):
        channels = [
            _ue(channel='LinkedIn'),
            _ue(channel='Substack', acquisition_cost=2000, revenue_attributed=8000),
        ]
        report = generate_multi_channel_report(channels)
        self.assertIn('LinkedIn', report)
        self.assertIn('Substack', report)

    def test_multi_channel_empty_list(self):
        report = generate_multi_channel_report([])
        self.assertIn('No channel data', report)

    def test_multi_channel_table_format(self):
        channels = [_ue(channel='LinkedIn')]
        report = generate_multi_channel_report(channels)
        self.assertIn('| Channel |', report)
        self.assertIn('| CAC |', report)
        self.assertIn('| ROMI |', report)


if __name__ == "__main__":
    unittest.main()
