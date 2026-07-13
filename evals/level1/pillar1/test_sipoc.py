"""
Level 1 eval: SIPOC generation
Tests FM-01 (incomplete SIPOC gate) and the completeness assertion.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))


class TestSIPOCGate:
    """FM-01: No CTQ tree without a complete SIPOC."""

    def test_sipoc_all_five_columns_required(self):
        from pillar1.sipoc import validate_sipoc

        incomplete = {
            "suppliers": ["Internal team"],
            "inputs": ["Client brief"],
            "process": ["Discovery → Analysis → Delivery"],
            "outputs": ["CTQ tree"],
            # "customers" missing
        }
        result = validate_sipoc(incomplete)
        assert result.is_valid is False
        assert "customers" in result.missing_columns

    def test_sipoc_empty_column_is_invalid(self):
        from pillar1.sipoc import validate_sipoc

        with_empty = {
            "suppliers": [],
            "inputs": ["Client brief"],
            "process": ["Discovery → Analysis → Delivery"],
            "outputs": ["CTQ tree"],
            "customers": ["VP Ops"],
        }
        result = validate_sipoc(with_empty)
        assert result.is_valid is False
        assert "suppliers" in result.empty_columns

    def test_complete_sipoc_passes_validation(self):
        from pillar1.sipoc import validate_sipoc

        complete = {
            "suppliers": ["Internal team", "Client data"],
            "inputs": ["Client brief", "Process data"],
            "process": ["Discovery → Analyse → Design → Deliver → Control"],
            "outputs": ["CTQ tree", "SIPOC document"],
            "customers": ["VP Ops", "COO"],
        }
        result = validate_sipoc(complete)
        assert result.is_valid is True

    def test_ctq_generation_blocked_without_complete_sipoc(self):
        from pillar1.ctq import generate_ctq_tree
        from pillar1.sipoc import SIPOCValidationError

        incomplete_sipoc = {
            "suppliers": ["Internal team"],
            "inputs": ["Client brief"],
            "process": ["Discovery"],
            "outputs": [],  # empty
            "customers": ["VP Ops"],
        }
        with pytest.raises(SIPOCValidationError):
            generate_ctq_tree(sipoc=incomplete_sipoc, service_context="Performance measurement")
