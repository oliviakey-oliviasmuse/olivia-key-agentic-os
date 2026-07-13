"""
Level 1 eval: Project Product Description generation
Tests FM-02 (subjective language), FM-04 (missing fields), FM-05 (quality check skipped).
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

SUBJECTIVE_BLOCKLIST = [
    "good", "clear", "professional", "appropriate", "reasonable",
    "high quality", "sufficient", "adequate", "timely", "well-structured",
    "effective", "suitable", "satisfactory",
]

REQUIRED_PPD_FIELDS = [
    "purpose", "composition", "derivation", "format",
    "quality_criteria", "acceptance_method",
]


class TestPPDStructure:
    """FM-04: PPD must have all six required fields."""

    def test_ppd_has_all_required_fields(self):
        from pillar1.ppd import generate_ppd

        ppd = generate_ppd(
            deliverable_name="CTQ Tree Document",
            engagement_context="Performance measurement for EV manufacturer",
        )
        for field in REQUIRED_PPD_FIELDS:
            assert field in ppd, f"PPD missing required field: {field}"
            assert ppd[field], f"PPD field '{field}' is empty"

    def test_ppd_with_missing_field_raises_error(self):
        from pillar1.ppd import validate_ppd, PPDValidationError

        incomplete_ppd = {
            "purpose": "Define measurable CTQ requirements",
            "composition": "CTQ nodes with LSL/USL tolerances",
            "derivation": "From SIPOC and client voice-of-customer data",
            "format": "PDF document, max 2 pages",
            "quality_criteria": "All nodes have numeric LSL and USL; zero subjective language",
            # "acceptance_method" missing
        }
        with pytest.raises(PPDValidationError) as exc_info:
            validate_ppd(incomplete_ppd)
        assert "acceptance_method" in str(exc_info.value)


class TestPPDQualityCriteria:
    """FM-02: Quality criteria must be objective and binary."""

    def test_subjective_language_is_flagged(self):
        from pillar1.ppd import check_quality_criteria_objectivity

        subjective_criteria = "Deliverable must be professionally presented and clear"
        result = check_quality_criteria_objectivity(subjective_criteria)
        assert result.is_objective is False
        assert len(result.flagged_terms) > 0

    def test_objective_criteria_passes(self):
        from pillar1.ppd import check_quality_criteria_objectivity

        objective_criteria = (
            "All CTQ nodes contain a numeric LSL and USL. "
            "Zero nodes use language from the subjective blocklist. "
            "Document is ≤2 pages."
        )
        result = check_quality_criteria_objectivity(objective_criteria)
        assert result.is_objective is True

    def test_blocklist_covers_known_terms(self):
        from pillar1.ppd import check_quality_criteria_objectivity

        for term in SUBJECTIVE_BLOCKLIST:
            result = check_quality_criteria_objectivity(f"Output must be {term}")
            assert result.is_objective is False, f"Blocklist missed term: '{term}'"


class TestPPDQualityCheck:
    """FM-05: Quality check must run and be logged in every PPD output."""

    def test_ppd_output_includes_quality_check_result(self):
        from pillar1.ppd import generate_ppd

        ppd = generate_ppd(
            deliverable_name="SIPOC Document",
            engagement_context="Supply chain optimisation for automotive OEM",
        )
        assert "quality_check_passed" in ppd, "quality_check_passed field missing from PPD output"
        assert ppd["quality_check_passed"] is None, (
            "Stub PPD must have quality_check_passed=None — not True; it has not been validated"
        )

    def test_failed_quality_check_is_surfaced_not_silenced(self):
        from pillar1.ppd import _test_only_ppd_with_subjective_criteria

        ppd = _test_only_ppd_with_subjective_criteria(
            deliverable_name="Test Deliverable",
            forced_criteria="Output must be professional and clear",
        )
        assert ppd["quality_check_passed"] is False
        assert "flagged_terms" in ppd
        assert len(ppd["flagged_terms"]) > 0
