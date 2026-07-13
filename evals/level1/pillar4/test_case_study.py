"""Tests for Pillar 4 Agent 2 — Case Study Writer."""
import pytest
from src.pillar4.case_study import (
    build_case_study,
    calculate_copq_reduction,
    calculate_roi,
    CoPQBreakdown,
    CaseStudyMetrics,
    ANONYMISED_NAME,
    DEFECT_CODES,
)


# ── Shared fixtures ────────────────────────────────────────────────────────

def base_inputs(**overrides):
    defaults = dict(
        client_name="Acme Aerospace",
        copq_baseline=14_000_000,
        copq_outcome=10_000_000,
        intervention="Deployed SIPOC, CTQ tree, and Control Plan across the assembly process.",
        client_approved=True,
    )
    defaults.update(overrides)
    return defaults


# ── Feature 1: Case Study Generation ─────────────────────────────────────

class TestCaseStudyGeneration:

    def test_happy_path_all_inputs_produces_pass(self):
        """All inputs provided → gate PASS, markdown contains all six sections."""
        result = build_case_study(**base_inputs(
            metrics=CaseStudyMetrics(ftar=94, nps=72),
            client_quote="Outstanding results.",
            lessons=["Start CTQ tree earlier", "Involve operators in FMEA"],
            date="2026-06-17",
        ))
        assert result.gate == "PASS"
        md = result.markdown
        assert "## Client Context" in md
        assert "## Problem Quantified" in md
        assert "## Intervention Applied" in md
        assert "## Measurable Outcome" in md
        assert "## Client Quote" in md
        assert "## Lessons Learned" in md

    def test_no_quote_produces_placeholder_not_error(self):
        """include_quote=True but no quote → placeholder text; no exception."""
        result = build_case_study(**base_inputs(lessons=["Lesson 1"]))
        assert result.gate == "PASS"
        assert "[No quote provided" in result.markdown

    def test_missing_baseline_raises_g1(self):
        """G1: copq_baseline=None → ValueError."""
        with pytest.raises(ValueError, match="G1"):
            build_case_study(**base_inputs(copq_baseline=None))

    def test_missing_outcome_raises_g1(self):
        """G1: copq_outcome=None → ValueError."""
        with pytest.raises(ValueError, match="G1"):
            build_case_study(**base_inputs(copq_outcome=None))

    def test_missing_intervention_raises_g2(self):
        """G2: intervention=None → ValueError."""
        with pytest.raises(ValueError, match="G2"):
            build_case_study(**base_inputs(intervention=None))

    def test_empty_intervention_string_raises_g2(self):
        """G2: whitespace-only intervention → ValueError."""
        with pytest.raises(ValueError, match="G2"):
            build_case_study(**base_inputs(intervention="   "))


# ── Feature 2: Gate Enforcement ───────────────────────────────────────────

class TestGateEnforcement:

    def test_g3_passes_when_ftar_provided(self):
        """G3: FTAR metric present → no G3 warning."""
        result = build_case_study(**base_inputs(
            metrics=CaseStudyMetrics(ftar=92), lessons=["L1"]
        ))
        assert not any("G3" in w for w in result.warnings)

    def test_g3_warning_when_no_metrics(self):
        """G3: no metrics and no engagement_cost → G3 warning; gate still PASS."""
        result = build_case_study(**base_inputs(lessons=["L1"]))
        assert result.gate == "PASS"
        assert any("G3" in w for w in result.warnings)

    def test_g3_not_triggered_when_engagement_cost_provided(self):
        """engagement_cost counts as a metric for G3 purposes (ROI calculable)."""
        result = build_case_study(**base_inputs(engagement_cost=150_000, lessons=["L1"]))
        assert not any("G3" in w for w in result.warnings)

    def test_e1_defect_when_not_approved(self):
        """E1: client_approved=False → E1 in defects; draft watermark in markdown."""
        result = build_case_study(**base_inputs(client_approved=False, lessons=["L1"]))
        assert any("E1" in d for d in result.defects)
        assert "DRAFT" in result.markdown

    def test_e1_cleared_when_approved(self):
        """client_approved=True → E1 not in defects; no draft watermark."""
        result = build_case_study(**base_inputs(lessons=["L1"]))
        assert not any("E1" in d for d in result.defects)
        assert "DRAFT" not in result.markdown

    def test_e3_defect_when_lessons_empty_and_included(self):
        """E3: include_lessons=True and no lessons → E3 in defects."""
        result = build_case_study(**base_inputs())
        assert any("E3" in d for d in result.defects)

    def test_e3_not_triggered_when_include_lessons_false(self):
        """E3 not raised when lessons section is explicitly excluded."""
        result = build_case_study(**base_inputs(include_lessons=False))
        assert not any("E3" in d for d in result.defects)

    def test_e3_not_triggered_when_lessons_provided(self):
        """E3 not raised when lessons list is non-empty."""
        result = build_case_study(**base_inputs(lessons=["Lesson 1", "Lesson 2"]))
        assert not any("E3" in d for d in result.defects)


# ── Feature 3: CoPQ Reduction Calculation ────────────────────────────────

class TestCoPQReductionCalculation:

    def test_standard_reduction_amount_and_percentage(self):
        """£14M → £10M = £4M reduction, 28.6%."""
        data = calculate_copq_reduction(14_000_000, 10_000_000)
        assert data["reduction"] == 4_000_000
        assert abs(data["pct"] - 28.571) < 0.01
        assert data["reversed"] is False

    def test_outcome_exceeds_baseline_sets_reversed_flag(self):
        """outcome > baseline → reversed = True."""
        data = calculate_copq_reduction(10_000_000, 12_000_000)
        assert data["reversed"] is True

    def test_reversed_copq_adds_warning_to_result(self):
        """Reversed CoPQ adds a warning to result.warnings."""
        result = build_case_study(**base_inputs(
            copq_baseline=10_000_000,
            copq_outcome=12_000_000,
            lessons=["L1"],
        ))
        assert any("CoPQ outcome exceeds baseline" in w for w in result.warnings)

    def test_roi_calculated_from_engagement_cost(self):
        """ROI = (reduction - cost) / cost × 100 when engagement_cost provided."""
        data = calculate_copq_reduction(14_000_000, 10_000_000)
        roi = calculate_roi(data["reduction"], 150_000)
        assert abs(roi - ((4_000_000 - 150_000) / 150_000 * 100)) < 0.01

    def test_roi_appears_in_markdown_when_cost_provided(self):
        """Engagement cost → ROI calculated and rendered in markdown."""
        result = build_case_study(**base_inputs(engagement_cost=150_000, lessons=["L1"]))
        assert "ROI:" in result.markdown

    def test_roi_absent_when_no_cost_and_no_metric(self):
        """No engagement_cost and no metrics.roi_pct → ROI absent from markdown."""
        result = build_case_study(**base_inputs(lessons=["L1"]))
        assert "ROI:" not in result.markdown

    def test_roi_from_metrics_takes_precedence(self):
        """metrics.roi_pct provided → used directly, engagement_cost ignored."""
        result = build_case_study(**base_inputs(
            metrics=CaseStudyMetrics(roi_pct=2500.0),
            engagement_cost=150_000,
            lessons=["L1"],
        ))
        assert "2500.0%" in result.markdown

    def test_zero_engagement_cost_returns_none_roi(self):
        """calculate_roi with cost=0 → None (no division by zero)."""
        assert calculate_roi(4_000_000, 0) is None

    def test_negative_engagement_cost_returns_none_roi(self):
        """calculate_roi with cost<0 → None."""
        assert calculate_roi(4_000_000, -1) is None


# ── Feature 4: Anonymisation ──────────────────────────────────────────────

class TestAnonymisation:

    def test_anonymise_false_uses_client_name(self):
        """anonymise=False → client name in markdown title."""
        result = build_case_study(**base_inputs(lessons=["L1"], anonymise=False))
        assert "Acme Aerospace" in result.markdown

    def test_anonymise_true_no_industry_uses_confidential_placeholder(self):
        """anonymise=True, no industry → ANONYMISED_NAME in title."""
        result = build_case_study(**base_inputs(lessons=["L1"], anonymise=True))
        assert ANONYMISED_NAME in result.markdown
        assert "Acme Aerospace" not in result.markdown

    def test_anonymise_true_with_industry_uses_industry_descriptor(self):
        """anonymise=True, industry provided → '[Aerospace Client]' in title."""
        result = build_case_study(**base_inputs(
            lessons=["L1"], anonymise=True, industry="Aerospace"
        ))
        assert "[Aerospace Client]" in result.markdown
        assert "Acme Aerospace" not in result.markdown


# ── Feature 5: Optional Sections ─────────────────────────────────────────

class TestOptionalSections:

    def test_include_quote_false_omits_section(self):
        """include_quote=False → no Client Quote section in markdown."""
        result = build_case_study(**base_inputs(lessons=["L1"], include_quote=False))
        assert "## Client Quote" not in result.markdown

    def test_include_lessons_false_omits_section(self):
        """include_lessons=False → no Lessons Learned section in markdown."""
        result = build_case_study(**base_inputs(include_lessons=False))
        assert "## Lessons Learned" not in result.markdown

    def test_include_quote_true_with_no_quote_shows_placeholder(self):
        """include_quote=True, client_quote=None → placeholder text in section."""
        result = build_case_study(**base_inputs(lessons=["L1"], include_quote=True))
        assert "## Client Quote" in result.markdown
        assert "[No quote provided" in result.markdown


# ── Feature 6: Render Output ──────────────────────────────────────────────

class TestRenderOutput:

    def test_approved_case_study_has_no_draft_watermark(self):
        """client_approved=True → no DRAFT watermark."""
        result = build_case_study(**base_inputs(lessons=["L1"]))
        assert "DRAFT" not in result.markdown

    def test_unapproved_case_study_has_draft_watermark(self):
        """client_approved=False → DRAFT watermark present."""
        result = build_case_study(**base_inputs(client_approved=False, lessons=["L1"]))
        assert "DRAFT" in result.markdown

    def test_date_rendered_when_provided(self):
        """date parameter appears in rendered markdown."""
        result = build_case_study(**base_inputs(lessons=["L1"], date="2026-06-17"))
        assert "2026-06-17" in result.markdown

    def test_copq_breakdown_renders_categories(self):
        """CoPQBreakdown with all categories → all four lines in Problem Quantified."""
        breakdown = CoPQBreakdown(
            internal=10_200_000, external=3_000_000,
            appraisal=600_000, prevention=200_000,
        )
        result = build_case_study(**base_inputs(copq_breakdown=breakdown, lessons=["L1"]))
        assert "Internal failure" in result.markdown
        assert "External failure" in result.markdown
        assert "Appraisal" in result.markdown
        assert "Prevention" in result.markdown

    def test_repeat_engagement_true_appears_in_outcome(self):
        """metrics.repeat_engagement=True → 'Repeat engagement: Yes' in markdown."""
        result = build_case_study(**base_inputs(
            metrics=CaseStudyMetrics(repeat_engagement=True), lessons=["L1"]
        ))
        assert "Repeat engagement: Yes" in result.markdown

    def test_next_steps_always_present(self):
        """## Next Steps section always rendered."""
        result = build_case_study(**base_inputs(lessons=["L1"]))
        assert "## Next Steps" in result.markdown

    def test_quote_with_attribution_rendered_correctly(self):
        """Client quote with attribution → formatted as 'quote' – attribution."""
        result = build_case_study(**base_inputs(
            client_quote="Transformational results.",
            quote_attribution="Jane Smith, COO",
            lessons=["L1"],
        ))
        assert '"Transformational results." – Jane Smith, COO' in result.markdown
