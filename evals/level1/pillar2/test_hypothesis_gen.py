import pytest
from src.pillar2.hypothesis_gen import (
    HypothesisPerformanceLog,
    DEFAULT_WEIGHTS,
    SCRAP_TRIGGER_THRESHOLD,
    WEIGHT_ADJUST_THRESHOLD,
    WEIGHT_FLOOR,
)


def _log_rank1_failure(log: HypothesisPerformanceLog, hyp_id: str, factor: str = 'information_gain'):
    log.log_feedback(
        hypothesis_id=hyp_id,
        rank=1,
        dominant_factor=factor,
        actual_engagement=0.01,
        predicted_engagement_low=0.03,
        predicted_engagement_high=0.05,
        actual_commercial_result=0,
    )


class TestHypothesisId:
    def test_id_starts_with_hyp_prefix(self):
        log = HypothesisPerformanceLog()
        hyp_id = log.generate_id(1)
        assert hyp_id.startswith('HYP-')

    def test_id_sequence_is_padded(self):
        log = HypothesisPerformanceLog()
        assert log.generate_id(1).endswith('-01')
        assert log.generate_id(2).endswith('-02')

    def test_id_contains_date_segment(self):
        log = HypothesisPerformanceLog()
        hyp_id = log.generate_id(1)
        parts = hyp_id.split('-')
        # HYP-YYYYMMDD-NN → 3 parts
        assert len(parts) == 3
        assert len(parts[1]) == 8  # YYYYMMDD


class TestRankingWeights:
    def test_default_weights_total(self):
        assert sum(DEFAULT_WEIGHTS.values()) == 10

    def test_score_all_factors_present(self):
        log = HypothesisPerformanceLog()
        factors = {k: True for k in DEFAULT_WEIGHTS}
        score, top = log.score_hypothesis(factors)
        assert score == 10
        # top factor must be one of the weight-2 factors
        assert top in ['information_gain', 'brand_authority', 'conversational_angle', 'first_party_data']

    def test_score_partial_factors(self):
        log = HypothesisPerformanceLog()
        score, top = log.score_hypothesis({'information_gain': True, 'cluster_gap': True})
        assert score == 3  # weight 2 + weight 1
        assert top == 'information_gain'

    def test_score_no_factors(self):
        log = HypothesisPerformanceLog()
        score, top = log.score_hypothesis({k: False for k in DEFAULT_WEIGHTS})
        assert score == 0
        assert top == ''


class TestWeightAdjustment:
    def test_no_adjustment_below_threshold(self):
        log = HypothesisPerformanceLog()
        for i in range(WEIGHT_ADJUST_THRESHOLD - 1):
            _log_rank1_failure(log, f'HYP-0{i}')
        assert not log.should_adjust_weights()

    def test_adjustment_triggered_at_threshold(self):
        log = HypothesisPerformanceLog()
        for i in range(WEIGHT_ADJUST_THRESHOLD):
            _log_rank1_failure(log, f'HYP-0{i}')
        assert log.should_adjust_weights()

    def test_failing_factor_weight_decreases(self):
        log = HypothesisPerformanceLog()
        original = log.weights['information_gain']
        log.adjust_weights('information_gain')
        assert log.weights['information_gain'] == original - 1

    def test_succeeding_factor_weight_increases(self):
        log = HypothesisPerformanceLog()
        original = log.weights['first_party_data']
        log.adjust_weights('information_gain', succeeding_factor='first_party_data')
        assert log.weights['first_party_data'] == original + 1

    def test_weight_does_not_fall_below_floor(self):
        log = HypothesisPerformanceLog()
        log.weights['cluster_gap'] = WEIGHT_FLOOR
        log.adjust_weights('cluster_gap')
        assert log.weights['cluster_gap'] == WEIGHT_FLOOR


class TestScrapTrigger:
    def test_no_scrap_below_threshold(self):
        log = HypothesisPerformanceLog()
        for i in range(SCRAP_TRIGGER_THRESHOLD - 1):
            _log_rank1_failure(log, f'HYP-0{i}')
        assert not log.should_scrap()

    def test_scrap_triggered_at_threshold(self):
        log = HypothesisPerformanceLog()
        for i in range(SCRAP_TRIGGER_THRESHOLD):
            _log_rank1_failure(log, f'HYP-0{i}')
        assert log.should_scrap()

    def test_scrap_recommendation_contains_keyword(self):
        log = HypothesisPerformanceLog()
        for i in range(SCRAP_TRIGGER_THRESHOLD):
            _log_rank1_failure(log, f'HYP-0{i}')
        rec = log.scrap_recommendation()
        assert rec is not None
        assert 'SCENARIO: HYPOTHESIS MODEL FAILURE' in rec

    def test_successful_rank1_resets_consecutive_count(self):
        log = HypothesisPerformanceLog()
        for i in range(SCRAP_TRIGGER_THRESHOLD - 1):
            _log_rank1_failure(log, f'HYP-0{i}')
        # A successful rank-1 hypothesis breaks the streak
        log.log_feedback(
            hypothesis_id='HYP-SUCCESS',
            rank=1,
            dominant_factor='first_party_data',
            actual_engagement=0.05,
            predicted_engagement_low=0.03,
            predicted_engagement_high=0.06,
            actual_commercial_result=2,
        )
        assert not log.should_scrap()

    def test_scrap_recommendation_is_none_before_threshold(self):
        log = HypothesisPerformanceLog()
        assert log.scrap_recommendation() is None
