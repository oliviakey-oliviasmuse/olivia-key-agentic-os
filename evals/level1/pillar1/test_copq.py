"""
Level 1 eval: CoPQ Pricing Calculator
Tests FM-03 (price floor), FM-06 (ROI without anchor), FM-07 (partial CoPQ as complete).
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

PRICE_FLOOR_MONTHLY = 5000  # £5,000/month — no exceptions


class TestCoPQCalculation:

    def test_explicit_zero_is_not_missing(self):
        """Defect-001: zero (confirmed none) must not be treated as missing (unknown)."""
        from pillar1.copq import calculate_copq

        result = calculate_copq(
            internal_failure=80000,
            external_failure=40000,
            appraisal=20000,
            prevention=0.0,  # client confirmed: no prevention spend
        )
        assert result.is_complete is True, "Explicit zero should not be counted as missing"
        assert "prevention" not in result.missing_categories
        assert result.total_annual_copq == 140000

    def test_none_is_missing_not_zero(self):
        """Defect-001: None (data not collected) must be flagged as missing."""
        from pillar1.copq import calculate_copq

        result = calculate_copq(
            internal_failure=80000,
            external_failure=40000,
            appraisal=20000,
            prevention=None,  # not asked — data not collected
        )
        assert result.is_complete is False
        assert "prevention" in result.missing_categories
        assert result.is_floor_estimate is True

    def test_all_four_categories_produces_complete_result(self):
        from pillar1.copq import calculate_copq

        result = calculate_copq(
            internal_failure=120000,
            external_failure=85000,
            appraisal=30000,
            prevention=15000,
        )
        assert result.total_annual_copq == 250000
        assert result.is_complete is True
        assert result.missing_categories == []

    def test_partial_categories_flagged_as_floor_estimate(self):
        """FM-07: Partial CoPQ must never be presented as a complete figure."""
        from pillar1.copq import calculate_copq

        result = calculate_copq(
            internal_failure=60000,
            external_failure=None,   # not provided
            appraisal=None,          # not provided
            prevention=10000,
        )
        assert result.is_complete is False
        assert result.is_floor_estimate is True
        assert "external_failure" in result.missing_categories
        assert "appraisal" in result.missing_categories

    def test_partial_copq_label_present_in_output(self):
        from pillar1.copq import calculate_copq

        result = calculate_copq(
            internal_failure=40000,
            external_failure=None,
            appraisal=20000,
            prevention=None,
        )
        assert result.is_floor_estimate is True
        assert result.total_label == "conservative floor estimate"


class TestPricingFloor:
    """FM-03: Price recommendation must never fall below £5,000/month."""

    def test_pricing_at_10_percent_of_copq(self):
        from pillar1.copq import generate_pricing_recommendation

        rec = generate_pricing_recommendation(annual_copq=600000)
        assert rec.low_monthly == 5000    # 10% of 600k / 12 = 5000
        assert rec.high_monthly == 10000  # 20% of 600k / 12 = 10000

    def test_floor_enforced_when_copq_is_low(self):
        """Low CoPQ produces sub-floor 10-20% — floor must override."""
        from pillar1.copq import generate_pricing_recommendation

        rec = generate_pricing_recommendation(annual_copq=120000)
        # 10% of 120k / 12 = 1000 — below floor
        # 20% of 120k / 12 = 2000 — below floor
        assert rec.low_monthly >= PRICE_FLOOR_MONTHLY
        assert rec.high_monthly >= PRICE_FLOOR_MONTHLY
        assert rec.floor_applied is True

    def test_pricing_recommendation_never_returns_sub_floor(self):
        from pillar1.copq import generate_pricing_recommendation

        for copq in [0, 1000, 10000, 50000, 100000]:
            rec = generate_pricing_recommendation(annual_copq=copq)
            assert rec.low_monthly >= PRICE_FLOOR_MONTHLY, (
                f"Price below floor for CoPQ={copq}: got £{rec.low_monthly}/month"
            )


class TestROINarrative:
    """FM-06: ROI narrative must contain a numeric CoPQ anchor."""

    def test_roi_narrative_contains_copq_figure(self):
        from pillar1.copq import generate_roi_narrative, calculate_copq

        copq_result = calculate_copq(
            internal_failure=200000,
            external_failure=100000,
            appraisal=40000,
            prevention=20000,
        )
        narrative = generate_roi_narrative(copq_result=copq_result, engagement_price_monthly=5000)
        assert narrative.copq_figure is not None
        assert isinstance(narrative.copq_figure, (int, float))
        assert narrative.copq_figure > 0

    def test_roi_narrative_cannot_be_generated_without_copq(self):
        from pillar1.copq import generate_roi_narrative, ROIAnchorError

        with pytest.raises(ROIAnchorError):
            generate_roi_narrative(copq_result=None, engagement_price_monthly=5000)

    def test_high_copq_triggers_validation_warning(self):
        """Any CoPQ >£5M flags as outlier requiring validation."""
        from pillar1.copq import calculate_copq

        result = calculate_copq(
            internal_failure=3000000,
            external_failure=2500000,
            appraisal=400000,
            prevention=200000,
        )
        assert result.total_annual_copq > 5000000
        assert result.requires_validation is True
        assert "outlier" in result.validation_warning.lower()
