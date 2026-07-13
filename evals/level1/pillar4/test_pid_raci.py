"""Tests for Pillar 4 Agent 0 — PID & RACI Generator."""
import pytest
from src.pillar4.pid_raci import (
    build_pid,
    validate_raci,
    QualityStandard,
    RACIRow,
    RiskRow,
    CommunicationEntry,
    DEFAULT_COMM_FREQUENCY,
    DEFAULT_COMM_FORMAT,
    DEFAULT_COMM_OWNER,
)


# ── Shared fixtures ────────────────────────────────────────────────────────

def make_quality_standards(n=3, with_ppd=True):
    return [
        QualityStandard(
            ctq=f"CTQ {i+1}",
            ppd_ref=f"PPD-{i+1:02d}" if with_ppd else None,
            lsl=80, usl=100, unit="%",
        )
        for i in range(n)
    ]


def make_raci_rows():
    return [
        RACIRow(
            deliverable="SIPOC & CTQ tree",
            responsible=["Olivia Key"],
            accountable=["Client Sponsor"],
            consulted=["Operations Manager"],
            informed=["Board"],
        ),
        RACIRow(
            deliverable="Control Plan",
            responsible=["Olivia Key"],
            accountable=["Client Sponsor"],
        ),
    ]


def base_inputs(**overrides):
    defaults = dict(
        client_name="Acme Aerospace",
        engagement_name="Hidden Factory Reduction",
        scope="Reduce hidden factory CoPQ by 25% within 6 months.",
        deliverables=["SIPOC & CTQ tree", "Control Plan", "Lessons Report"],
        quality_standards=make_quality_standards(),
        raci_rows=make_raci_rows(),
        signed_off=True,
    )
    defaults.update(overrides)
    return defaults


# ── Feature 1: PID Generation ─────────────────────────────────────────────

class TestPIDGeneration:

    def test_happy_path_all_sections_present(self):
        """All inputs → gate PASS; markdown contains required sections."""
        result = build_pid(**base_inputs(date="2026-06-17"))
        assert result.gate == "PASS"
        md = result.markdown
        assert "## Project Overview" in md
        assert "## Quality Standards" in md
        assert "## Risks" in md
        assert "## Communication Plan" in md
        assert "## RACI Matrix" in md
        assert "## Sign-off" in md

    def test_include_raci_false_omits_raci_section(self):
        """include_raci=False → no RACI Matrix section."""
        result = build_pid(**base_inputs(include_raci=False))
        assert "## RACI Matrix" not in result.markdown

    def test_include_communication_plan_false_omits_section(self):
        """include_communication_plan=False → no Communication Plan section."""
        result = build_pid(**base_inputs(include_communication_plan=False))
        assert "## Communication Plan" not in result.markdown

    def test_include_risks_false_omits_section(self):
        """include_risks=False → no Risks section."""
        result = build_pid(**base_inputs(include_risks=False))
        assert "## Risks" not in result.markdown

    def test_missing_client_name_raises_g1(self):
        """G1: empty client_name → ValueError."""
        with pytest.raises(ValueError, match="G1"):
            build_pid(**base_inputs(client_name=""))

    def test_missing_scope_raises_g1(self):
        """G1: empty scope → ValueError."""
        with pytest.raises(ValueError, match="G1"):
            build_pid(**base_inputs(scope=""))

    def test_empty_deliverables_raises_g1(self):
        """G1: empty deliverables list → ValueError."""
        with pytest.raises(ValueError, match="G1"):
            build_pid(**base_inputs(deliverables=[]))


# ── Feature 2: Gate Enforcement ───────────────────────────────────────────

class TestGateEnforcement:

    def test_g2_fewer_than_3_standards_raises(self):
        """G2: 2 quality standards → ValueError."""
        with pytest.raises(ValueError, match="G2"):
            build_pid(**base_inputs(quality_standards=make_quality_standards(2)))

    def test_g2_exactly_3_standards_passes(self):
        """G2: exactly 3 quality standards → no error."""
        result = build_pid(**base_inputs(quality_standards=make_quality_standards(3)))
        assert result.gate == "PASS"

    def test_g2_more_than_3_standards_passes(self):
        """G2: 5 quality standards → no error."""
        result = build_pid(**base_inputs(quality_standards=make_quality_standards(5)))
        assert result.gate == "PASS"

    def test_g3_raci_row_missing_responsible_adds_warning(self):
        """G3: RACI row with no responsible → D2 warning."""
        rows = [RACIRow(deliverable="SIPOC", responsible=[], accountable=["Sponsor"])]
        result = build_pid(**base_inputs(raci_rows=rows))
        assert any("D2" in w and "Responsible" in w for w in result.warnings)
        assert result.gate == "PASS"

    def test_g3_raci_row_missing_accountable_adds_warning(self):
        """G3: RACI row with no accountable → D2 warning."""
        rows = [RACIRow(deliverable="SIPOC", responsible=["Olivia"], accountable=[])]
        result = build_pid(**base_inputs(raci_rows=rows))
        assert any("D2" in w and "Accountable" in w for w in result.warnings)
        assert result.gate == "PASS"

    def test_d3_quality_standard_without_ppd_ref_adds_defect(self):
        """D3: quality standard with no ppd_ref → D3 in defects."""
        standards = make_quality_standards(3, with_ppd=False)
        result = build_pid(**base_inputs(quality_standards=standards))
        assert any("D3" in d for d in result.defects)
        assert result.gate == "PASS"

    def test_d3_not_raised_when_all_standards_have_ppd(self):
        """No D3 when all quality standards have ppd_ref."""
        result = build_pid(**base_inputs(quality_standards=make_quality_standards(3, with_ppd=True)))
        assert not any("D3" in d for d in result.defects)


# ── Feature 3: RACI Validation ────────────────────────────────────────────

class TestRACIValidation:

    def test_complete_raci_rows_return_no_warnings(self):
        """validate_raci() returns empty list when all rows are complete."""
        warnings = validate_raci(make_raci_rows())
        assert warnings == []

    def test_missing_responsible_returns_warning(self):
        """validate_raci() flags row with no responsible."""
        rows = [RACIRow(deliverable="Control Plan", responsible=[], accountable=["Sponsor"])]
        warnings = validate_raci(rows)
        assert len(warnings) == 1
        assert "Responsible" in warnings[0]

    def test_missing_accountable_returns_warning(self):
        """validate_raci() flags row with no accountable."""
        rows = [RACIRow(deliverable="Control Plan", responsible=["Olivia"], accountable=[])]
        warnings = validate_raci(rows)
        assert len(warnings) == 1
        assert "Accountable" in warnings[0]

    def test_raci_not_validated_when_include_raci_false(self):
        """G3 not evaluated when include_raci=False — no D2 warnings."""
        rows = [RACIRow(deliverable="Control Plan", responsible=[], accountable=[])]
        result = build_pid(**base_inputs(raci_rows=rows, include_raci=False))
        assert not any("D2" in w for w in result.warnings)


# ── Feature 4: Quality Standards ─────────────────────────────────────────

class TestQualityStandards:

    def test_standards_with_ppd_refs_render_ppd_in_output(self):
        """PPD ref appears in Quality Standards section."""
        result = build_pid(**base_inputs(quality_standards=make_quality_standards(3, with_ppd=True)))
        assert "PPD-01" in result.markdown

    def test_standards_without_ppd_render_not_linked(self):
        """Standard without ppd_ref shows 'PPD: not linked'."""
        standards = make_quality_standards(3, with_ppd=False)
        result = build_pid(**base_inputs(quality_standards=standards))
        assert "PPD: not linked" in result.markdown

    def test_lsl_usl_rendered_in_quality_standards(self):
        """LSL and USL values appear in the Quality Standards section."""
        standards = [
            QualityStandard(ctq="On-time rate", ppd_ref="PPD-01", lsl=90, usl=100, unit="%"),
            QualityStandard(ctq="Defect rate", ppd_ref="PPD-02", lsl=0, usl=2, unit="%"),
            QualityStandard(ctq="FTAR", ppd_ref="PPD-03", lsl=85, usl=100, unit="%"),
        ]
        result = build_pid(**base_inputs(quality_standards=standards))
        assert "LSL: 90" in result.markdown
        assert "USL: 100" in result.markdown


# ── Feature 5: Risk Section ───────────────────────────────────────────────

class TestRiskSection:

    def test_risks_render_as_table(self):
        """Provided risks appear in the Risks section as a markdown table."""
        risks = [
            RiskRow(mode="No operator buy-in", rpn=192, mitigation="Stakeholder workshops"),
            RiskRow(mode="Data integration fails", rpn=84, mitigation="IT pre-engagement check"),
        ]
        result = build_pid(**base_inputs(risks=risks))
        assert "No operator buy-in" in result.markdown
        assert "192" in result.markdown
        assert "Stakeholder workshops" in result.markdown

    def test_include_risks_false_omits_section(self):
        """include_risks=False → Risks section not rendered."""
        result = build_pid(**base_inputs(include_risks=False))
        assert "## Risks" not in result.markdown

    def test_no_risks_provided_shows_placeholder(self):
        """include_risks=True but no risks → placeholder text."""
        result = build_pid(**base_inputs(risks=[], include_risks=True))
        assert "[No risks provided" in result.markdown


# ── Feature 6: Communication Plan ────────────────────────────────────────

class TestCommunicationPlan:

    def test_custom_comm_entry_renders_correctly(self):
        """Custom CommunicationEntry values appear in Communication Plan section."""
        comm = CommunicationEntry(
            frequency="Fortnightly",
            format="Status report",
            owner="Lead Consultant",
            attendees=["VP Ops", "Project Sponsor"],
        )
        result = build_pid(**base_inputs(communication=comm))
        assert "Fortnightly" in result.markdown
        assert "Status report" in result.markdown
        assert "VP Ops" in result.markdown

    def test_default_comm_entry_used_when_none_provided(self):
        """No communication arg → defaults rendered in section."""
        result = build_pid(**base_inputs(communication=None))
        assert DEFAULT_COMM_FREQUENCY in result.markdown
        assert DEFAULT_COMM_OWNER in result.markdown

    def test_include_communication_plan_false_omits_section(self):
        """include_communication_plan=False → no Communication Plan section."""
        result = build_pid(**base_inputs(include_communication_plan=False))
        assert "## Communication Plan" not in result.markdown


# ── Feature 7: Render Output ──────────────────────────────────────────────

class TestRenderOutput:

    def test_include_approval_true_shows_signoff_section(self):
        """include_approval=True → Sign-off section present."""
        result = build_pid(**base_inputs(include_approval=True))
        assert "## Sign-off" in result.markdown
        assert "Approved by Acme Aerospace" in result.markdown

    def test_include_approval_false_omits_signoff_section(self):
        """include_approval=False → no Sign-off section."""
        result = build_pid(**base_inputs(include_approval=False))
        assert "## Sign-off" not in result.markdown

    def test_signed_off_false_shows_pending_notice(self):
        """signed_off=False → PENDING SIGN-OFF notice in markdown."""
        result = build_pid(**base_inputs(signed_off=False))
        assert "PENDING SIGN-OFF" in result.markdown
        assert result.signed_off is False

    def test_signed_off_true_omits_pending_notice(self):
        """signed_off=True → no pending notice; result.signed_off=True."""
        result = build_pid(**base_inputs(signed_off=True))
        assert "PENDING SIGN-OFF" not in result.markdown
        assert result.signed_off is True

    def test_date_rendered_when_provided(self):
        """date parameter appears in rendered markdown."""
        result = build_pid(**base_inputs(date="2026-06-17"))
        assert "2026-06-17" in result.markdown

    def test_timeline_rendered_when_provided(self):
        """timeline_start and timeline_end appear in Project Overview."""
        result = build_pid(**base_inputs(timeline_start="2026-07-01", timeline_end="2026-12-31"))
        assert "2026-07-01" in result.markdown
        assert "2026-12-31" in result.markdown

    def test_client_name_in_title(self):
        """Client name appears in PID document title."""
        result = build_pid(**base_inputs())
        assert "# Project Initiation Document – Acme Aerospace" in result.markdown

    def test_raci_rows_render_responsible_and_accountable(self):
        """RACI row content appears in the RACI Matrix table."""
        result = build_pid(**base_inputs())
        assert "Olivia Key" in result.markdown
        assert "Client Sponsor" in result.markdown


# ── Generator API tests (import via re-export from pid_raci) ─────────────

import unittest
from src.pillar4.pid_raci import (
    Deliverable,
    generate_pid,
    validate_pid,
    raci_matrix_markdown,
    pid_markdown,
    PID,
)


class TestPIDRACILLM(unittest.TestCase):

    def test_generate_pid(self):
        deliverables = [Deliverable(name='Report', responsible='Consultant', accountable='Client')]
        pid = generate_pid(
            client='Acme',
            engagement='Project',
            scope='Reduce CoPQ',
            deliverables=deliverables,
            quality_standards=['CTQ 1', 'CTQ 2'],
        )
        self.assertEqual(pid.client, 'Acme')
        self.assertEqual(len(pid.deliverables), 1)
        self.assertEqual(pid.deliverables[0].name, 'Report')

    def test_validate_pid_missing_client(self):
        pid = PID(client='', engagement='Project', scope='Scope', deliverables=[], quality_standards=[])
        errors = validate_pid(pid)
        self.assertIn('Client or engagement name missing', errors)

    def test_validate_pid_missing_deliverable_role(self):
        d = Deliverable(name='Report', responsible='', accountable='')
        pid = PID(client='Acme', engagement='Project', scope='Scope', deliverables=[d], quality_standards=['Q'])
        errors = validate_pid(pid)
        self.assertIn("Deliverable 'Report' has no Responsible or Accountable", errors)

    def test_raci_matrix_markdown(self):
        d = Deliverable(name='Report', responsible='Consultant', accountable='Client', consulted='Ops', informed='Team')
        md = raci_matrix_markdown([d])
        self.assertIn('Report', md)
        self.assertIn('Consultant', md)
        self.assertIn('Client', md)

    def test_pid_markdown(self):
        d = Deliverable(name='Report', responsible='Consultant', accountable='Client')
        pid = generate_pid(
            client='Acme',
            engagement='Project',
            scope='Reduce CoPQ',
            deliverables=[d],
            quality_standards=['CTQ 1'],
        )
        md = pid_markdown(pid)
        self.assertIn('Acme', md)
        self.assertIn('Reduce CoPQ', md)
        self.assertIn('Report', md)
        self.assertIn('RACI Matrix', md)

    def test_empty_deliverables_raci(self):
        md = raci_matrix_markdown([])
        self.assertEqual(md, 'No deliverables provided.')
