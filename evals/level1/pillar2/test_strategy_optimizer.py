import pytest
from datetime import date, timedelta
from src.pillar2.strategy_optimizer import (
    calculate_kpi_change,
    check_andon_efficiency_crisis,
    check_andon_negative_roi,
    check_andon_data_gap,
    check_g1_data_sources,
    normalise_attribution,
    linear_forecast,
    generate_kpi_dashboard,
    StrategyOptimizerError,
)


class TestKpiChange:
    def test_cac_increase_returns_red(self):
        pct, status = calculate_kpi_change(562, 450, higher_is_better=False)
        assert status == 'RED'
        assert pct > 0

    def test_cac_decrease_returns_green(self):
        pct, status = calculate_kpi_change(380, 450, higher_is_better=False)
        assert status == 'GREEN'
        assert pct < 0

    def test_conversion_improvement_returns_green(self):
        _, status = calculate_kpi_change(0.030, 0.023, higher_is_better=True)
        assert status == 'GREEN'

    def test_marginal_change_within_5pct_returns_amber(self):
        _, status = calculate_kpi_change(0.024, 0.023, higher_is_better=True)
        assert status == 'AMBER'

    def test_zero_previous_returns_amber_and_zero_pct(self):
        pct, status = calculate_kpi_change(100, 0, higher_is_better=True)
        assert status == 'AMBER'
        assert pct == 0.0

    def test_roi_drop_returns_red(self):
        _, status = calculate_kpi_change(0.05, 0.18, higher_is_better=True)
        assert status == 'RED'

    def test_exact_5pct_improvement_is_amber_not_green(self):
        # exactly at the AMBER_BAND boundary — not strictly > 5%
        _, status = calculate_kpi_change(105, 100, higher_is_better=True)
        assert status == 'AMBER'

    def test_just_over_5pct_improvement_is_green(self):
        _, status = calculate_kpi_change(106, 100, higher_is_better=True)
        assert status == 'GREEN'


class TestAndonEfficiencyCrisis:
    def test_both_conditions_fire(self):
        assert check_andon_efficiency_crisis(25.0, -12.0) is True

    def test_only_cac_increase_does_not_fire(self):
        # CAC up but conversion only -5% — below -10% threshold
        assert check_andon_efficiency_crisis(25.0, -5.0) is False

    def test_only_conv_drop_does_not_fire(self):
        # Conversion down but CAC only +10% — below +20% threshold
        assert check_andon_efficiency_crisis(10.0, -15.0) is False

    def test_both_at_exact_threshold_does_not_fire(self):
        # Must be strictly greater than 20 / less than -10
        assert check_andon_efficiency_crisis(20.0, -10.0) is False


class TestAndonNegativeRoi:
    def test_two_consecutive_negatives_fire(self):
        assert check_andon_negative_roi([-0.05, -0.03]) is True

    def test_last_two_negative_with_earlier_positive_fires(self):
        # Early positive doesn't matter — last 2 are negative
        assert check_andon_negative_roi([0.10, -0.05, -0.03]) is True

    def test_one_negative_period_does_not_fire(self):
        assert check_andon_negative_roi([-0.05]) is False

    def test_last_period_positive_does_not_fire(self):
        assert check_andon_negative_roi([-0.05, 0.02]) is False

    def test_empty_history_does_not_fire(self):
        assert check_andon_negative_roi([]) is False


class TestAndonDataGap:
    def test_gap_over_7_days_fires(self):
        today = date.today()
        last_seen = {'website': today - timedelta(days=8)}
        fired, gaps = check_andon_data_gap(last_seen, today, critical_sources={'website'})
        assert fired is True
        assert 'website' in gaps

    def test_gap_within_7_days_does_not_fire(self):
        today = date.today()
        last_seen = {'website': today - timedelta(days=3)}
        fired, _ = check_andon_data_gap(last_seen, today, critical_sources={'website'})
        assert fired is False

    def test_exactly_7_days_does_not_fire(self):
        # boundary: >7, not >=7
        today = date.today()
        last_seen = {'website': today - timedelta(days=7)}
        fired, _ = check_andon_data_gap(last_seen, today, critical_sources={'website'})
        assert fired is False

    def test_gap_isolated_to_affected_source(self):
        today = date.today()
        last_seen = {
            'website': today - timedelta(days=10),  # gap
            'crm':     today - timedelta(days=1),   # fine
        }
        fired, gaps = check_andon_data_gap(
            last_seen, today, critical_sources={'website', 'crm'}
        )
        assert fired is True
        assert 'website' in gaps
        assert 'crm' not in gaps


class TestG1DataSources:
    def test_three_sources_passes(self):
        feed = {
            'website': {'sessions': 1000},
            'crm':     {'leads': 5},
            'social':  {'linkedin': {'engagement_rate': 0.034}},
        }
        passed, count = check_g1_data_sources(feed)
        assert passed is True
        assert count == 3

    def test_two_sources_fails(self):
        feed = {'website': {'sessions': 1000}, 'crm': {'leads': 5}}
        passed, count = check_g1_data_sources(feed)
        assert passed is False
        assert count == 2

    def test_five_sources_passes(self):
        feed = {
            'website':  {'sessions': 1000},
            'crm':      {'leads': 5},
            'social':   {'linkedin': {}},
            'email':    {'open_rate': 0.32},
            'paid_ads': {'spend': 100},
        }
        passed, count = check_g1_data_sources(feed)
        assert passed is True
        assert count == 5

    def test_empty_dict_source_not_counted(self):
        # crm is present but empty — falsy, does not count
        feed = {'website': {'sessions': 1000}, 'crm': {}, 'social': {'linkedin': {}}}
        passed, count = check_g1_data_sources(feed)
        assert count == 2
        assert passed is False


class TestG4Attribution:
    def test_sums_to_1_unchanged(self):
        attr = {'linkedin': 0.45, 'organic': 0.30, 'direct': 0.15, 'other': 0.10}
        result = normalise_attribution(attr)
        assert abs(sum(result.values()) - 1.0) < 0.001

    def test_sums_over_1_normalised_to_100pct(self):
        attr = {'linkedin': 0.50, 'organic': 0.40, 'direct': 0.30}  # sums to 1.20
        result = normalise_attribution(attr)
        assert abs(sum(result.values()) - 1.0) < 0.001

    def test_empty_returns_empty(self):
        assert normalise_attribution({}) == {}

    def test_single_channel_becomes_100pct(self):
        result = normalise_attribution({'linkedin': 0.75})
        assert result['linkedin'] == 1.0


class TestLinearForecast:
    def test_upward_trend_forecasts_higher_than_last(self):
        assert linear_forecast([100, 110, 120]) > 120

    def test_downward_trend_forecasts_lower_than_last(self):
        assert linear_forecast([100, 90, 80]) < 80

    def test_flat_trend_returns_same_value(self):
        assert abs(linear_forecast([100.0, 100.0, 100.0]) - 100.0) < 0.01

    def test_single_value_returns_same(self):
        assert linear_forecast([42.0]) == 42.0

    def test_two_point_trend_extrapolates_correctly(self):
        result = linear_forecast([10.0, 20.0])
        assert abs(result - 30.0) < 0.01

    def test_empty_list_raises(self):
        with pytest.raises(StrategyOptimizerError):
            linear_forecast([])


class TestKpiDashboard:
    CURRENT  = {'cac': 450, 'conversion_rate': 0.023, 'roi': 0.18, 'clv': 8500, 'engagement_rate': 0.034}
    PREVIOUS = {'cac': 400, 'conversion_rate': 0.020, 'roi': 0.15, 'clv': 8000, 'engagement_rate': 0.030}

    def test_returns_five_rows(self):
        rows = generate_kpi_dashboard(self.CURRENT, self.PREVIOUS)
        assert len(rows) == 5

    def test_cac_increase_flagged_red(self):
        current  = {**self.CURRENT,  'cac': 560}
        previous = {**self.PREVIOUS, 'cac': 400}
        rows = generate_kpi_dashboard(current, previous)
        cac_row = next(r for r in rows if 'CAC' in r['label'])
        assert cac_row['status'] == 'RED'

    def test_roi_improvement_flagged_green(self):
        current  = {**self.CURRENT,  'roi': 0.25}
        previous = {**self.PREVIOUS, 'roi': 0.15}
        rows = generate_kpi_dashboard(current, previous)
        roi_row = next(r for r in rows if r['label'] == 'ROI')
        assert roi_row['status'] == 'GREEN'

    def test_missing_kpi_returns_amber_with_none_values(self):
        rows = generate_kpi_dashboard({'cac': 400}, {'cac': 350})
        missing = [r for r in rows if r['current'] is None]
        assert len(missing) == 4
        assert all(r['status'] == 'AMBER' for r in missing)

    def test_change_pct_calculated_correctly(self):
        current  = {**self.CURRENT,  'roi': 0.20}
        previous = {**self.PREVIOUS, 'roi': 0.10}
        rows = generate_kpi_dashboard(current, previous)
        roi_row = next(r for r in rows if r['label'] == 'ROI')
        assert roi_row['change_pct'] == 100.0
