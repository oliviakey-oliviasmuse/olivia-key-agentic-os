import pytest
from pathlib import Path
from src.pillar3.scorecard import (
    generate_questions,
    calculate_score,
    max_score,
    validate_scorecard,
    recommend,
    build_scorecard_markdown,
    ScorecardError,
    THRESHOLD_PASS,
    THRESHOLD_DEFER_LOW,
    THRESHOLD_PASS_WARM,
    THRESHOLD_DEFER_LOW_WARM,
    RECOMMENDATION_PROCEED,
    RECOMMENDATION_DEFER,
    RECOMMENDATION_REJECT,
    QUESTIONS_DEFAULT,
)
from src.pillar3.outreach_log import append_log_entry


# ---------------------------------------------------------------------------
# TestGenerateQuestions
# ---------------------------------------------------------------------------

class TestGenerateQuestions:
    def test_copq_health_default_count_returns_8(self):
        questions = generate_questions('CoPQ_Health', 8)
        assert len(questions) == 8

    def test_hidden_factory_5_questions(self):
        questions = generate_questions('Hidden_Factory', 5)
        assert len(questions) == 5

    def test_ops_maturity_10_questions(self):
        questions = generate_questions('Ops_Maturity', 10)
        assert len(questions) == 10

    def test_questions_above_max_raises(self):
        with pytest.raises(ScorecardError):
            generate_questions('CoPQ_Health', 11)

    def test_questions_below_min_raises(self):
        with pytest.raises(ScorecardError):
            generate_questions('CoPQ_Health', 4)

    def test_unknown_scorecard_type_raises(self):
        with pytest.raises(ScorecardError):
            generate_questions('Legacy_Audit', 8)


# ---------------------------------------------------------------------------
# TestCalculateScore
# ---------------------------------------------------------------------------

class TestCalculateScore:
    def test_all_max_scores_8_questions_returns_24(self):
        assert calculate_score([3] * 8) == 24

    def test_all_zeros_returns_zero(self):
        assert calculate_score([0] * 8) == 0

    def test_mixed_scores_sum_correctly(self):
        # 3+2+1+0+3+2+1+0 = 12
        assert calculate_score([3, 2, 1, 0, 3, 2, 1, 0]) == 12

    def test_score_above_3_raises(self):
        with pytest.raises(ScorecardError):
            calculate_score([3, 3, 4, 3, 3, 3, 3, 3])

    def test_negative_score_raises(self):
        with pytest.raises(ScorecardError):
            calculate_score([3, -1, 3, 3, 3, 3, 3, 3])


# ---------------------------------------------------------------------------
# TestMaxScore
# ---------------------------------------------------------------------------

class TestMaxScore:
    def test_5_questions_max_is_15(self):
        assert max_score(5) == 15

    def test_8_questions_max_is_24(self):
        assert max_score(8) == 24

    def test_10_questions_max_is_30(self):
        assert max_score(10) == 30


# ---------------------------------------------------------------------------
# TestRecommendation
# ---------------------------------------------------------------------------

class TestRecommendation:
    def test_above_threshold_returns_proceed(self):
        code, _ = recommend(20)
        assert code == RECOMMENDATION_PROCEED

    def test_at_threshold_boundary_returns_proceed(self):
        code, _ = recommend(THRESHOLD_PASS)
        assert code == RECOMMENDATION_PROCEED

    def test_one_below_threshold_returns_defer(self):
        code, _ = recommend(THRESHOLD_PASS - 1)
        assert code == RECOMMENDATION_DEFER

    def test_mid_defer_range_returns_defer(self):
        code, _ = recommend(14)
        assert code == RECOMMENDATION_DEFER

    def test_at_defer_lower_boundary_returns_defer(self):
        code, _ = recommend(THRESHOLD_DEFER_LOW)
        assert code == RECOMMENDATION_DEFER

    def test_one_below_defer_lower_returns_reject(self):
        code, _ = recommend(THRESHOLD_DEFER_LOW - 1)
        assert code == RECOMMENDATION_REJECT

    def test_zero_score_returns_reject(self):
        code, _ = recommend(0)
        assert code == RECOMMENDATION_REJECT


# ---------------------------------------------------------------------------
# TestWarmLeadRecommendation
# ---------------------------------------------------------------------------

class TestWarmLeadRecommendation:
    """Warm lead thresholds: PROCEED ≥14, DEFER 8–13, REJECT <8."""

    _DM = ['inbound_dm']
    _DOWNLOAD = ['gated_content_download']
    _MULTI = ['inbound_dm', 'requested_call']

    def test_warm_at_14_returns_proceed(self):
        code, _ = recommend(14, warm_lead_signals=self._DM)
        assert code == RECOMMENDATION_PROCEED

    def test_warm_above_14_returns_proceed(self):
        code, _ = recommend(20, warm_lead_signals=self._DM)
        assert code == RECOMMENDATION_PROCEED

    def test_warm_13_returns_defer(self):
        code, _ = recommend(13, warm_lead_signals=self._DM)
        assert code == RECOMMENDATION_DEFER

    def test_warm_at_defer_lower_boundary_8_returns_defer(self):
        code, _ = recommend(8, warm_lead_signals=self._DOWNLOAD)
        assert code == RECOMMENDATION_DEFER

    def test_warm_7_returns_reject(self):
        code, _ = recommend(7, warm_lead_signals=self._DM)
        assert code == RECOMMENDATION_REJECT

    def test_warm_zero_returns_reject(self):
        code, _ = recommend(0, warm_lead_signals=self._DM)
        assert code == RECOMMENDATION_REJECT

    def test_cold_14_still_returns_defer(self):
        """Score 14 is warm-PROCEED but cold-DEFER — no signals means cold thresholds apply."""
        code, _ = recommend(14)
        assert code == RECOMMENDATION_DEFER

    def test_cold_12_still_returns_defer(self):
        """Score 12 is cold-DEFER — should not become PROCEED without warm signals."""
        code, _ = recommend(12)
        assert code == RECOMMENDATION_DEFER

    def test_sarah_chen_inbound_dm_returns_defer(self):
        """Score 12 + warm signal = DEFER. Warm threshold is ≥14; 12 is in the warm DEFER band (8–13)."""
        code, _ = recommend(12, warm_lead_signals=['inbound_dm'])
        assert code == RECOMMENDATION_DEFER

    def test_explanation_contains_warm_signals(self):
        _, text = recommend(12, warm_lead_signals=['inbound_dm', 'requested_call'])
        assert 'inbound_dm' in text
        assert 'requested_call' in text

    def test_explanation_contains_warm_threshold(self):
        _, text = recommend(14, warm_lead_signals=self._DM)
        assert str(THRESHOLD_PASS_WARM) in text

    def test_cold_explanation_contains_cold_threshold(self):
        _, text = recommend(20)
        assert str(THRESHOLD_PASS) in text

    def test_invalid_signal_raises(self):
        with pytest.raises(ScorecardError):
            recommend(12, warm_lead_signals=['legacy_audit'])

    def test_multiple_warm_signals_accepted(self):
        """Score 14 with multiple warm signals → PROCEED (at exact warm threshold boundary)."""
        code, _ = recommend(14, warm_lead_signals=list(self._MULTI))
        assert code == RECOMMENDATION_PROCEED


# ---------------------------------------------------------------------------
# TestValidateScorecard
# ---------------------------------------------------------------------------

class TestValidateScorecard:
    def test_valid_8_questions_8_responses(self):
        questions = ['q'] * 8
        responses = [2] * 8
        assert validate_scorecard(questions, responses) is True

    def test_response_count_mismatch_raises(self):
        with pytest.raises(ScorecardError):
            validate_scorecard(['q'] * 8, [2] * 7)

    def test_questions_below_min_raises(self):
        with pytest.raises(ScorecardError):
            validate_scorecard(['q'] * 4, [2] * 4)

    def test_questions_above_max_raises(self):
        with pytest.raises(ScorecardError):
            validate_scorecard(['q'] * 11, [2] * 11)


# ---------------------------------------------------------------------------
# TestScorecardMarkdown
# ---------------------------------------------------------------------------

class TestScorecardMarkdown:
    QUESTIONS = generate_questions('CoPQ_Health', 8)

    def test_contains_prospect_name(self):
        md = build_scorecard_markdown('Jane Williams', 'Steel Works Ltd', self.QUESTIONS)
        assert 'Jane Williams' in md

    def test_unanswered_scorecard_has_correct_row_count(self):
        md = build_scorecard_markdown('Jane Williams', 'Steel Works Ltd', self.QUESTIONS)
        # 8 question rows + 1 total row = 9 rows with pipe prefix (excluding header rows)
        data_rows = [ln for ln in md.splitlines() if ln.startswith('|') and '---' not in ln]
        # header row + 8 question rows + total row = 10
        assert len(data_rows) == 10

    def test_unanswered_contains_copy_instruction(self):
        md = build_scorecard_markdown('Jane Williams', 'Steel Works Ltd', self.QUESTIONS)
        assert 'copy this table' in md.lower()

    def test_completed_scorecard_contains_recommendation(self):
        responses = [3, 2, 3, 2, 3, 2, 3, 2]  # total = 20 → PROCEED
        md = build_scorecard_markdown(
            'Jane Williams', 'Steel Works Ltd', self.QUESTIONS, responses=responses
        )
        assert 'PROCEED' in md
        assert 'copy this table' not in md.lower()

    def test_completed_total_row_shows_score_and_max(self):
        responses = [2] * 8  # total = 16
        md = build_scorecard_markdown(
            'Jane Williams', 'Steel Works Ltd', self.QUESTIONS, responses=responses
        )
        assert '16/24' in md

    def test_warm_signals_shown_and_produce_proceed(self):
        """Score 12 cold=DEFER but warm=PROCEED; markdown must reflect the correct outcome."""
        responses = [2, 1, 1, 2, 1, 2, 0, 3]  # total = 12
        md = build_scorecard_markdown(
            'Sarah Chen', 'Acme Aerospace', self.QUESTIONS,
            responses=responses,
            warm_lead_signals=['inbound_dm', 'requested_call'],
        )
        assert 'Warm' in md
        assert 'inbound_dm' in md
        assert 'PROCEED' in md

    def test_cold_lead_shows_cold_label(self):
        responses = [3] * 8  # total = 24 → cold PROCEED
        md = build_scorecard_markdown('Jane Williams', 'Steel Works Ltd', self.QUESTIONS, responses=responses)
        assert 'Cold' in md


# ---------------------------------------------------------------------------
# TestOutreachLog
# ---------------------------------------------------------------------------

class TestOutreachLog:
    def test_creates_file_if_not_exists(self, tmp_path):
        log_file = tmp_path / 'outreach_log.md'
        append_log_entry(
            prospect_name='John Smith',
            company='Acme Manufacturing',
            scorecard_type='CoPQ_Health',
            total_score=20,
            max_score=24,
            recommendation='PROCEED',
            log_file=log_file,
        )
        assert log_file.exists()

    def test_second_entry_appended_not_overwritten(self, tmp_path):
        log_file = tmp_path / 'outreach_log.md'
        for name in ('Prospect A', 'Prospect B'):
            append_log_entry(
                prospect_name=name,
                company='Test Co',
                scorecard_type='CoPQ_Health',
                total_score=14,
                max_score=24,
                recommendation='DEFER',
                log_file=log_file,
            )
        content = log_file.read_text()
        assert 'Prospect A' in content
        assert 'Prospect B' in content

    def test_entry_contains_prospect_name(self, tmp_path):
        log_file = tmp_path / 'outreach_log.md'
        append_log_entry(
            prospect_name='Rachel Chen',
            company='EV Dynamics Ltd',
            scorecard_type='Hidden_Factory',
            total_score=8,
            max_score=24,
            recommendation='REJECT',
            log_file=log_file,
        )
        assert 'Rachel Chen' in log_file.read_text()

    def test_warm_signals_written_to_log(self, tmp_path):
        log_file = tmp_path / 'outreach_log.md'
        append_log_entry(
            prospect_name='Sarah Chen',
            company='Acme Aerospace',
            scorecard_type='CoPQ_Health',
            total_score=12,
            max_score=24,
            recommendation='PROCEED',
            warm_lead_signals=['inbound_dm', 'requested_call'],
            log_file=log_file,
        )
        content = log_file.read_text()
        assert 'Warm' in content
        assert 'inbound_dm' in content
        assert '14' in content  # warm threshold

    def test_cold_lead_log_shows_cold_threshold(self, tmp_path):
        log_file = tmp_path / 'outreach_log.md'
        append_log_entry(
            prospect_name='John Smith',
            company='Steel Works Ltd',
            scorecard_type='CoPQ_Health',
            total_score=20,
            max_score=24,
            recommendation='PROCEED',
            log_file=log_file,
        )
        content = log_file.read_text()
        assert 'Cold' in content
        assert '18' in content  # cold threshold
