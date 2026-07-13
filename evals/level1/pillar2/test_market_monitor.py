import pytest
from src.pillar2.market_monitor import (
    score_commercial_potential,
    TrendAccuracyLog,
    SyntheticEngagementTracker,
    FALSE_SIGNAL_THRESHOLD,
    SYNTHETIC_CONSECUTIVE_WEEKS,
    SYNTHETIC_ENGAGEMENT_THRESHOLD,
)


class TestCommercialPotentialScore:
    def test_high_band_score_9(self):
        assert score_commercial_potential(9) == 'high'

    def test_high_band_boundary(self):
        assert score_commercial_potential(8) == 'high'

    def test_mid_band_score_6(self):
        assert score_commercial_potential(6) == 'mid'

    def test_mid_band_boundary(self):
        assert score_commercial_potential(5) == 'mid'

    def test_low_band_score_2(self):
        assert score_commercial_potential(2) == 'low'

    def test_score_above_10_raises(self):
        with pytest.raises(ValueError):
            score_commercial_potential(11)

    def test_score_zero_raises(self):
        with pytest.raises(ValueError):
            score_commercial_potential(0)


class TestTrendAccuracyLog:
    def test_no_warning_below_threshold(self):
        log = TrendAccuracyLog()
        for i in range(FALSE_SIGNAL_THRESHOLD - 1):
            log.log(f'Week {i}', 'Reddit', f'Trend {i}', False)
        assert log.check_false_signal_warning('Reddit') is None

    def test_warning_fires_at_threshold(self):
        log = TrendAccuracyLog()
        for i in range(FALSE_SIGNAL_THRESHOLD):
            log.log(f'Week {i}', 'Reddit', f'Trend {i}', False)
        warning = log.check_false_signal_warning('Reddit')
        assert warning is not None
        assert 'Reddit' in warning
        assert 'false signals' in warning

    def test_successful_signals_do_not_count(self):
        log = TrendAccuracyLog()
        log.log('Week 1', 'LinkedIn', 'Trend A', True)
        log.log('Week 2', 'LinkedIn', 'Trend B', True)
        assert log.check_false_signal_warning('LinkedIn') is None

    def test_false_signals_are_source_isolated(self):
        log = TrendAccuracyLog()
        for i in range(FALSE_SIGNAL_THRESHOLD):
            log.log(f'Week {i}', 'Reddit', f'Trend {i}', False)
        # Reddit has 3 false signals; LinkedIn has none
        assert log.check_false_signal_warning('LinkedIn') is None


class TestSyntheticEngagementTracker:
    def test_no_trigger_below_consecutive_threshold(self):
        tracker = SyntheticEngagementTracker()
        for _ in range(SYNTHETIC_CONSECUTIVE_WEEKS - 1):
            tracker.record_week('X', 0.85)
        assert tracker.check_scrap_trigger('X') is None

    def test_trigger_at_consecutive_threshold(self):
        tracker = SyntheticEngagementTracker()
        for _ in range(SYNTHETIC_CONSECUTIVE_WEEKS):
            tracker.record_week('X', 0.85)
        result = tracker.check_scrap_trigger('X')
        assert result is not None
        assert 'CRITICAL' in result
        assert 'X' in result

    def test_low_synthetic_week_resets_streak(self):
        tracker = SyntheticEngagementTracker()
        for _ in range(SYNTHETIC_CONSECUTIVE_WEEKS - 1):
            tracker.record_week('LinkedIn', 0.85)
        tracker.record_week('LinkedIn', 0.50)  # breaks the streak
        for _ in range(SYNTHETIC_CONSECUTIVE_WEEKS - 1):
            tracker.record_week('LinkedIn', 0.90)
        assert tracker.check_scrap_trigger('LinkedIn') is None

    def test_trigger_is_platform_isolated(self):
        tracker = SyntheticEngagementTracker()
        for _ in range(SYNTHETIC_CONSECUTIVE_WEEKS):
            tracker.record_week('X', 0.85)
        assert tracker.check_scrap_trigger('LinkedIn') is None

    def test_exact_threshold_boundary(self):
        # Rate exactly at SYNTHETIC_ENGAGEMENT_THRESHOLD counts as high
        tracker = SyntheticEngagementTracker()
        for _ in range(SYNTHETIC_CONSECUTIVE_WEEKS):
            tracker.record_week('Substack', SYNTHETIC_ENGAGEMENT_THRESHOLD)
        assert tracker.check_scrap_trigger('Substack') is not None
