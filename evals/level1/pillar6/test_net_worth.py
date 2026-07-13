import unittest
from src.pillar6.net_worth import (
    NetWorthSnapshot,
    compute_accumulation,
    check_accumulation_target,
    asset_allocation_trigger,
    generate_snapshot_report,
)


def _snap(date='2026-06-25', sipp=0.0, isa=0.0, liquidity=0.0, retained=0.0, profit=None):
    return NetWorthSnapshot(
        date=date, sipp=sipp, isa=isa,
        liquidity=liquidity, retained_earnings=retained,
        business_net_profit=profit,
    )


class TestNetWorthSnapshot(unittest.TestCase):
    def test_valid_snapshot_total(self):
        snap = _snap(sipp=50000, isa=30000, liquidity=20000, retained=10000)
        self.assertEqual(snap.total, 110000)

    def test_total_is_sum_of_components(self):
        snap = _snap(sipp=1000, isa=2000, liquidity=3000, retained=4000)
        self.assertEqual(snap.total, 10000)

    def test_default_target_and_threshold(self):
        snap = _snap()
        self.assertEqual(snap.target_accumulation, 2917.0)
        self.assertEqual(snap.threshold_profit, 6000.0)

    def test_zero_values_valid(self):
        snap = _snap()
        self.assertEqual(snap.total, 0.0)


class TestGateEnforcement(unittest.TestCase):
    def test_g1_invalid_date(self):
        with self.assertRaises(ValueError) as ctx:
            _snap(date='2026-99-99')
        self.assertIn('G1', str(ctx.exception))

    def test_g1_malformed_date_string(self):
        with self.assertRaises(ValueError) as ctx:
            _snap(date='not-a-date')
        self.assertIn('G1', str(ctx.exception))

    def test_g1_empty_date(self):
        with self.assertRaises(ValueError) as ctx:
            _snap(date='')
        self.assertIn('G1', str(ctx.exception))

    def test_g2_negative_sipp(self):
        with self.assertRaises(ValueError) as ctx:
            _snap(sipp=-1)
        self.assertIn('G2', str(ctx.exception))

    def test_g2_negative_isa(self):
        with self.assertRaises(ValueError) as ctx:
            _snap(isa=-100)
        self.assertIn('G2', str(ctx.exception))

    def test_g2_negative_liquidity(self):
        with self.assertRaises(ValueError) as ctx:
            _snap(liquidity=-500)
        self.assertIn('G2', str(ctx.exception))

    def test_g2_negative_retained_earnings(self):
        with self.assertRaises(ValueError) as ctx:
            _snap(retained=-10)
        self.assertIn('G2', str(ctx.exception))

    def test_g2_negative_business_net_profit(self):
        with self.assertRaises(ValueError) as ctx:
            _snap(profit=-1)
        self.assertIn('G2', str(ctx.exception))


class TestComputeAccumulation(unittest.TestCase):
    def test_positive_accumulation(self):
        # current.total = 110000, previous.total = 99000 → 11000
        current = _snap(sipp=50000, isa=30000, liquidity=20000, retained=10000)
        previous = _snap(sipp=45000, isa=28000, liquidity=18000, retained=8000)
        self.assertEqual(compute_accumulation(current, previous), 11000)

    def test_negative_accumulation(self):
        # current = 75000, previous = 98000 → -23000
        current = _snap(sipp=40000, isa=20000, liquidity=10000, retained=5000)
        previous = _snap(sipp=50000, isa=25000, liquidity=15000, retained=8000)
        self.assertEqual(compute_accumulation(current, previous), -23000)

    def test_zero_accumulation(self):
        snap = _snap(sipp=10000, isa=5000, liquidity=3000, retained=2000)
        self.assertEqual(compute_accumulation(snap, snap), 0.0)


class TestAccumulationTarget(unittest.TestCase):
    def test_on_track(self):
        self.assertEqual(check_accumulation_target(3000, 2917), "ON TRACK")

    def test_on_track_at_exact_boundary(self):
        # exactly 2917 → ON TRACK (>= is inclusive)
        self.assertEqual(check_accumulation_target(2917, 2917), "ON TRACK")

    def test_below_target(self):
        self.assertEqual(check_accumulation_target(2000, 2917), "BELOW TARGET")

    def test_below_target_just_under(self):
        self.assertEqual(check_accumulation_target(2916.99, 2917), "BELOW TARGET")

    def test_negative_accumulation_is_below_target(self):
        self.assertEqual(check_accumulation_target(-500, 2917), "BELOW TARGET")


class TestAssetAllocationTrigger(unittest.TestCase):
    def test_trigger_above_threshold(self):
        snap = _snap(profit=7000)
        result = asset_allocation_trigger(snap)
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result['sipp'], 3500.0)
        self.assertAlmostEqual(result['isa'], 2100.0)
        self.assertAlmostEqual(result['liquidity'], 1400.0)

    def test_no_trigger_below_threshold(self):
        snap = _snap(profit=5000)
        self.assertIsNone(asset_allocation_trigger(snap))

    def test_no_trigger_at_exact_threshold(self):
        # exactly 6000 → no trigger (> not >=)
        snap = _snap(profit=6000)
        self.assertIsNone(asset_allocation_trigger(snap))

    def test_no_trigger_profit_is_none(self):
        snap = _snap(profit=None)
        self.assertIsNone(asset_allocation_trigger(snap))

    def test_allocation_sums_to_profit(self):
        snap = _snap(profit=9000)
        result = asset_allocation_trigger(snap)
        self.assertAlmostEqual(result['sipp'] + result['isa'] + result['liquidity'], 9000.0)

    def test_allocation_percentages(self):
        snap = _snap(profit=10000)
        result = asset_allocation_trigger(snap)
        self.assertAlmostEqual(result['sipp'], 5000.0)   # 50%
        self.assertAlmostEqual(result['isa'], 3000.0)    # 30%
        self.assertAlmostEqual(result['liquidity'], 2000.0)  # 20%


class TestSnapshotReport(unittest.TestCase):
    def test_report_contains_date(self):
        snap = _snap(date='2026-06-25', sipp=50000, isa=30000, liquidity=20000, retained=10000)
        report = generate_snapshot_report(snap)
        self.assertIn('2026-06-25', report)

    def test_report_contains_total(self):
        snap = _snap(sipp=50000, isa=30000, liquidity=20000, retained=10000)
        report = generate_snapshot_report(snap)
        self.assertIn('£110,000.00', report)

    def test_report_contains_components(self):
        snap = _snap(sipp=50000, isa=30000, liquidity=20000, retained=10000)
        report = generate_snapshot_report(snap)
        self.assertIn('SIPP: £50,000.00', report)
        self.assertIn('ISA: £30,000.00', report)
        self.assertIn('Liquidity: £20,000.00', report)
        self.assertIn('Retained Earnings: £10,000.00', report)

    def test_report_g3_warning_when_no_previous(self):
        snap = _snap(sipp=10000)
        report = generate_snapshot_report(snap)
        self.assertIn('G3 WARNING', report)

    def test_report_with_previous_on_track(self):
        # current = 110000, previous = 99000 → accumulation = 11000 > 2917 → ON TRACK
        current = _snap(sipp=50000, isa=30000, liquidity=20000, retained=10000)
        previous = _snap(sipp=45000, isa=28000, liquidity=18000, retained=8000)
        report = generate_snapshot_report(current, previous)
        self.assertIn('£11,000.00', report)
        self.assertIn('ON TRACK', report)

    def test_report_with_previous_below_target(self):
        current = _snap(sipp=50000)
        previous = _snap(sipp=49000)
        report = generate_snapshot_report(current, previous)
        self.assertIn('BELOW TARGET', report)

    def test_report_accumulation_label_present(self):
        current = _snap(sipp=50000, isa=30000, liquidity=20000, retained=10000)
        previous = _snap(sipp=45000, isa=28000, liquidity=18000, retained=8000)
        report = generate_snapshot_report(current, previous)
        self.assertIn('Accumulation (vs previous month): £11,000.00', report)

    def test_report_allocation_trigger_yes(self):
        snap = _snap(profit=7000)
        report = generate_snapshot_report(snap)
        self.assertIn('Asset Allocation Trigger: Yes', report)
        self.assertIn('SIPP: £3,500.00 (50%)', report)
        self.assertIn('ISA: £2,100.00 (30%)', report)
        self.assertIn('Liquidity: £1,400.00 (20%)', report)

    def test_report_allocation_trigger_no(self):
        snap = _snap(profit=4000)
        report = generate_snapshot_report(snap)
        self.assertIn('Asset Allocation Trigger: No', report)

    def test_report_allocation_trigger_no_when_profit_none(self):
        snap = _snap()
        report = generate_snapshot_report(snap)
        self.assertIn('Asset Allocation Trigger: No', report)


if __name__ == "__main__":
    unittest.main()
