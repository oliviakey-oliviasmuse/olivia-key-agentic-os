import pytest
from src.pillar2.content_gate import (
    check_g2_copq_terms,
    check_g5_word_count,
    check_g10_vanity_metrics,
    check_g12_hype_words,
    check_g13_sources,
    check_g16_commercial_cta,
    check_g17_funnel_alignment,
    extract_named_sources,
    run_programmatic_gates,
    generate_content_id,
    aggregate_verdict,
    GateResult,
    ContentGateError,
    ANDON_GATES,
)


class TestG2CoPQTerms:
    def test_happy_path_single_term(self):
        result = check_g2_copq_terms("The rework cost is destroying your margin.")
        assert result.passed is True

    def test_happy_path_compound_term(self):
        result = check_g2_copq_terms("Hidden factory costs are never measured.")
        assert result.passed is True

    def test_edge_case_copq_acronym(self):
        result = check_g2_copq_terms("CoPQ is the root cause of margin erosion.")
        assert result.passed is True

    def test_failure_no_term(self):
        result = check_g2_copq_terms("This post is about leadership and culture.")
        assert result.passed is False
        assert result.defect_code == 'M2'


class TestG5WordCount:
    def test_hygiene_happy_path(self):
        text = ' '.join(['word'] * 200)
        result = check_g5_word_count(text, 'Hygiene')
        assert result.passed is True

    def test_hub_happy_path(self):
        text = ' '.join(['word'] * 500)
        result = check_g5_word_count(text, 'Hub')
        assert result.passed is True

    def test_hero_happy_path(self):
        text = ' '.join(['word'] * 1100)
        result = check_g5_word_count(text, 'Hero')
        assert result.passed is True

    def test_hub_at_upper_tolerance_boundary(self):
        # 800 * 1.20 = 960 — should pass
        text = ' '.join(['word'] * 950)
        result = check_g5_word_count(text, 'Hub')
        assert result.passed is True

    def test_hub_exceeds_upper_tolerance(self):
        # > 960 words → FAIL
        text = ' '.join(['word'] * 1000)
        result = check_g5_word_count(text, 'Hub')
        assert result.passed is False
        assert result.defect_code == 'M5'

    def test_unknown_tier_raises(self):
        with pytest.raises(ContentGateError):
            check_g5_word_count("some text", 'Unknown')


class TestG10VanityMetrics:
    def test_happy_path_no_vanity(self):
        result = check_g10_vanity_metrics("CoPQ recovery drives enterprise value.")
        assert result.passed is True

    def test_failure_compound_vanity_phrase(self):
        result = check_g10_vanity_metrics("Get more likes and grow your followers with this approach.")
        assert result.passed is False

    def test_edge_followers_in_non_vanity_context(self):
        # "followers" alone is not in VANITY_TERMS — only compound phrases trigger
        result = check_g10_vanity_metrics("I asked my network of followers to test this.")
        assert result.passed is True


class TestG12HypeWords:
    def test_happy_path_clean_content(self):
        result = check_g12_hype_words("Operational measurement systems reduce defect rates by 40%.")
        assert result.passed is True

    def test_failure_revolutionary(self):
        result = check_g12_hype_words("This revolutionary framework changes everything.")
        assert result.passed is False
        assert result.defect_code == 'M7'

    def test_failure_ultimate(self):
        result = check_g12_hype_words("The ultimate guide to operational measurement.")
        assert result.passed is False

    def test_edge_partial_word_no_match(self):
        # 'best' must not match inside 'biggest' — word boundary enforced
        result = check_g12_hype_words("The biggest challenge in operations is measurement.")
        assert result.passed is True

    def test_g12_is_andon_gate(self):
        assert 'G12' in ANDON_GATES


class TestG16CommercialCTA:
    def test_enquiries_dm_me(self):
        result = check_g16_commercial_cta("If this resonates, DM me and we'll talk.", 'enquiries')
        assert result.passed is True

    def test_enquiries_book_a_call(self):
        result = check_g16_commercial_cta("Book a call to see your CoPQ exposure.", 'enquiries')
        assert result.passed is True

    def test_paid_subscribers_subscribe(self):
        result = check_g16_commercial_cta("Subscribe for £15/month to get the full breakdown.", 'paid_subscribers')
        assert result.passed is True

    def test_client_calls_calendar(self):
        result = check_g16_commercial_cta("Here's my calendar — let's talk.", 'client_calls')
        assert result.passed is True

    def test_brand_awareness_no_cta_required(self):
        result = check_g16_commercial_cta("No CTA here at all.", 'brand_awareness')
        assert result.passed is True

    def test_enquiries_missing_cta_fails_with_m10(self):
        result = check_g16_commercial_cta("Hope you found this useful!", 'enquiries')
        assert result.passed is False
        assert result.defect_code == 'M10'

    def test_unknown_objective_raises(self):
        with pytest.raises(ContentGateError):
            check_g16_commercial_cta("Some text", 'unknown_objective')


class TestG13Sources:
    # --- Happy path: case study format ---

    def test_case_study_i_analysed_with_percentage_passes(self):
        result = check_g13_sources(
            "I analysed 12 months of production data. Rework dropped from 18% to 9%."
        )
        assert result.passed is True

    def test_case_study_my_client_with_pound_outcome_passes(self):
        result = check_g13_sources(
            "My client reduced scrap cost by £340,000 per quarter after the intervention."
        )
        assert result.passed is True

    def test_case_study_i_helped_with_percentage_and_time_passes(self):
        result = check_g13_sources(
            "I helped them rewrite work instructions. Defects fell 40% in three months."
        )
        assert result.passed is True

    def test_case_study_i_discovered_with_copq_percentage_passes(self):
        result = check_g13_sources(
            "I discovered hidden factory accounted for 8% of total CoPQ at the supplier."
        )
        assert result.passed is True

    def test_case_study_we_applied_with_weekly_time_period_passes(self):
        result = check_g13_sources(
            "We applied these fixes. Within six weeks, rework dropped from 18% to 9%."
        )
        assert result.passed is True

    # --- Happy path: named sources with verification ---

    def test_named_institution_with_verified_sources_passes(self):
        result = check_g13_sources(
            "According to an MIT study, quality failures cost manufacturers 5% of revenue.",
            verified_sources=['MIT'],
        )
        assert result.passed is True

    def test_multiple_named_institutions_all_verified_passes(self):
        result = check_g13_sources(
            "The Gartner 2025 Report and McKinsey research both found rework costs exceed 5%.",
            verified_sources=['Gartner', 'McKinsey'],
        )
        assert result.passed is True

    # --- Happy path: generic keyword count (no named sources) ---

    def test_exactly_at_external_threshold_boundary_passes(self):
        # study + research + according to = exactly 3
        result = check_g13_sources(
            "This study and research show that according to the evidence this is true."
        )
        assert result.passed is True

    # --- Edge cases ---

    def test_first_party_language_without_verifiable_outcomes_fails(self):
        # "I analysed" present but no £, %, or time period with digits
        result = check_g13_sources(
            "I analysed the situation and discovered some interesting patterns."
        )
        assert result.passed is False

    def test_verifiable_outcomes_without_first_party_language_treated_as_general(self):
        # Has numbers (18%, £340k) but no first-party phrase — general post path
        result = check_g13_sources(
            "Companies typically see 18% rework rates and £340k in annual scrap costs."
        )
        assert result.passed is False

    def test_two_external_keywords_without_case_study_fails(self):
        result = check_g13_sources(
            "This study shows the research is clear on the topic."
        )
        assert result.passed is False

    def test_general_post_no_sources_fails(self):
        result = check_g13_sources(
            "Hidden factory costs are a major issue in capital-intensive manufacturing."
        )
        assert result.passed is False

    # --- Failure case: named sources without verification ---

    def test_named_institution_without_verified_sources_fails(self):
        result = check_g13_sources(
            "According to an MIT study, quality failures cost manufacturers 5% of revenue."
        )
        assert result.passed is False

    def test_partially_verified_named_sources_fails(self):
        # Gartner verified but McKinsey not — should still fail
        result = check_g13_sources(
            "The Gartner 2025 Report and McKinsey research both found rework costs exceed 5%.",
            verified_sources=['Gartner'],
        )
        assert result.passed is False

    # --- Failure case: ANDON gate behaviour ---

    def test_g13_is_registered_as_andon_gate(self):
        assert 'G13' in ANDON_GATES

    def test_g13_failure_fires_andon_in_aggregate(self):
        no_source_text = "Hidden factory costs are a major issue in manufacturing operations."
        g13_fail = check_g13_sources(no_source_text)
        assert g13_fail.passed is False
        assert g13_fail.is_andon_gate is True
        verdict, _, _ = aggregate_verdict([GateResult('G2', True), g13_fail])
        assert verdict == 'ANDON STOP'

    def test_g13_pass_does_not_fire_andon(self):
        case_study_text = "I analysed 12 months of data. Rework fell from 18% to 9% in six weeks."
        g13_pass = check_g13_sources(case_study_text)
        assert g13_pass.passed is True
        verdict, _, _ = aggregate_verdict([GateResult('G2', True), g13_pass])
        assert verdict == 'PASS'


class TestContentId:
    def test_id_includes_explicit_slug(self):
        cid = generate_content_id("The rework cost is destroying your margin.", slug='rework-cost')
        assert 'rework-cost' in cid

    def test_id_auto_slug_from_content(self):
        cid = generate_content_id("Hidden factory costs in EV manufacturing.")
        assert len(cid) > 10

    def test_id_contains_timestamp(self):
        cid = generate_content_id("some content", slug='test')
        assert 'T' in cid  # ISO timestamp marker


class TestExtractNamedSources:
    def test_extracts_known_institution_near_document_keyword(self):
        sources = extract_named_sources("According to an MIT study, quality failures cost 5%.")
        assert 'MIT' in sources

    def test_does_not_extract_institution_without_document_keyword(self):
        # MIT mentioned but no document keyword in same sentence
        sources = extract_named_sources("MIT is based in Cambridge, Massachusetts.")
        assert 'MIT' not in sources

    def test_extracts_dr_name_pattern(self):
        sources = extract_named_sources(
            "Dr. Jane Smith found that rework costs exceed £1m annually."
        )
        assert any('Jane' in s or 'Dr.' in s for s in sources)

    def test_extracts_year_prefixed_titled_document(self):
        sources = extract_named_sources("The 2024 Gartner Quality Cost Report shows a 20% rise.")
        assert len(sources) > 0

    def test_deduplicates_repeated_institution(self):
        sources = extract_named_sources(
            "MIT research confirms this. The MIT study was published in 2024."
        )
        assert sources.count('MIT') == 1

    def test_no_named_sources_returns_empty(self):
        sources = extract_named_sources(
            "This study and research show that according to the evidence this is true."
        )
        assert sources == []


class TestG17FunnelAlignment:
    # Happy path

    def test_hygiene_brand_awareness_tofu_passes(self):
        result = check_g17_funnel_alignment(
            "Rework costs are eating your margins.", 'Hygiene', 'brand_awareness'
        )
        assert result.passed is True

    def test_hub_paid_subscribers_mofu_passes(self):
        result = check_g17_funnel_alignment(
            "I analysed 12 months of data. Rework dropped 40% in three months.",
            'Hub', 'paid_subscribers',
        )
        assert result.passed is True

    def test_hero_enquiries_bofu_with_first_party_passes(self):
        text = "I helped a Tier-1 supplier recover £340,000 in six months. DM me to explore."
        result = check_g17_funnel_alignment(text, 'Hero', 'enquiries')
        assert result.passed is True

    def test_hub_enquiries_mofu_objective_not_blocked(self):
        # Hub=MOFU, enquiries=BOFU — only TOFU→BOFU is a hard block; MOFU→BOFU is allowed
        text = "I helped a client reduce rework by 40% in three months. DM me to explore."
        result = check_g17_funnel_alignment(text, 'Hub', 'enquiries')
        assert result.passed is True

    # Failure: TOFU content with BOFU objective

    def test_hygiene_enquiries_tofu_bofu_mismatch_fails_m11(self):
        result = check_g17_funnel_alignment(
            "Rework costs are eating your margins.", 'Hygiene', 'enquiries'
        )
        assert result.passed is False
        assert result.defect_code == 'M11'

    def test_hygiene_client_calls_tofu_bofu_mismatch_fails_m11(self):
        result = check_g17_funnel_alignment(
            "Hidden factory costs are rarely measured.", 'Hygiene', 'client_calls'
        )
        assert result.passed is False
        assert result.defect_code == 'M11'

    # Failure: BOFU content without first-party data

    def test_hero_enquiries_bofu_no_first_party_fails_m11(self):
        result = check_g17_funnel_alignment(
            "Research shows manufacturers lose 5% of revenue to quality failures. Get in touch.",
            'Hero', 'enquiries',
        )
        assert result.passed is False
        assert result.defect_code == 'M11'

    def test_hero_client_calls_bofu_no_first_party_fails_m11(self):
        result = check_g17_funnel_alignment(
            "Studies suggest rework costs exceed £500k in capital-intensive plants. Book a call.",
            'Hero', 'client_calls',
        )
        assert result.passed is False
        assert result.defect_code == 'M11'

    # Edge cases

    def test_unknown_tier_raises(self):
        with pytest.raises(ContentGateError):
            check_g17_funnel_alignment("Some content.", 'Premium', 'enquiries')

    def test_unknown_objective_raises(self):
        with pytest.raises(ContentGateError):
            check_g17_funnel_alignment("Some content.", 'Hub', 'upsell')


class TestAggregateVerdict:
    def test_all_pass_returns_pass(self):
        results = [GateResult(f'G{i}', True) for i in range(1, 6)]
        verdict, rate, defects = aggregate_verdict(results)
        assert verdict == 'PASS'
        assert rate == 1.0
        assert defects == []

    def test_one_non_andon_fail_returns_fail(self):
        results = [GateResult('G2', True), GateResult('G5', False, '', 'M5')]
        verdict, rate, defects = aggregate_verdict(results)
        assert verdict == 'FAIL'
        assert 'M5' in defects

    def test_andon_gate_fail_returns_andon_stop(self):
        results = [
            GateResult('G2', True),
            GateResult('G5', True),
            GateResult('G12', False, 'Hype word detected', 'M7'),
        ]
        verdict, rate, defects = aggregate_verdict(results)
        assert verdict == 'ANDON STOP'
        assert 'M7' in defects

    def test_many_non_andon_failures_returns_fail_not_andon(self):
        # Many failures but none are ANDON gates → FAIL, not ANDON STOP
        results = (
            [GateResult(f'G{i}', True) for i in range(1, 4)]
            + [GateResult(f'G{i}', False, '', 'M2') for i in range(4, 11)]
        )
        verdict, rate, defects = aggregate_verdict(results)
        assert verdict == 'FAIL'
        assert rate < 1.0
