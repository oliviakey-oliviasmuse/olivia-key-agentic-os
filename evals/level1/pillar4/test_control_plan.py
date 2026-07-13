"""Tests for Pillar 4 Agent 1 — Delivery Control Plan Generator."""
import pytest
from src.pillar4.control_plan import (
    build_delivery_control_plan,
    validate_ctq_coverage,
    render_control_plan_md,
    ControlPlanResult,
    DEFAULT_OWNER,
    DEFAULT_FREQUENCY_ANDON,
    DEFAULT_FREQUENCY_ACTION,
    DEFAULT_FREQUENCY_PLACEHOLDER,
    DEFAULT_REACTION_PLAN,
    RPN_ANDON_THRESHOLD,
)


# ── Shared fixtures ────────────────────────────────────────────────────────

class CTQNode:
    """Minimal stand-in matching P1 CTQNode shape."""
    def __init__(self, output, ctq, unit, lsl, usl, target=None):
        self.output = output
        self.ctq = ctq
        self.unit = unit
        self.lsl = lsl
        self.usl = usl
        self.target = target


def make_ctq_nodes():
    return [
        CTQNode("Delivery accuracy", "On-time delivery rate", "% deliverables on time", 90, 100),
        CTQNode("Report quality", "Report acceptance rate", "% reports accepted first time", 85, 100),
        CTQNode("Operator adoption", "Training completion rate", "% operators trained", 80, 100),
    ]


def make_fmea_results():
    return [
        {
            "mode": "No operator buy-in",
            "severity": 8, "occurrence": 6, "detection": 4,
            "rpn": 192, "classification": "ACTION",
            "action": "Mitigate – add control plan or reduce risk",
        },
        {
            "mode": "Management priority shift",
            "severity": 9, "occurrence": 5, "detection": 2,
            "rpn": 90, "classification": "ACCEPT",
            "action": "Accept – monitor",
        },
    ]


def make_ctq_mapping():
    return {"No operator buy-in": "Training completion rate"}


def make_andon_fmea():
    return [
        {
            "mode": "Critical system failure",
            "severity": 10, "occurrence": 6, "detection": 5,
            "rpn": 300, "classification": "ANDON",
            "action": "STOP – redesign or mitigate before proposal",
        },
    ]


# ── Feature 1: Strict mode — happy path and basic logic ──────────────────

class TestStrictMode:

    def test_happy_path_returns_pass_with_action_rows_only(self):
        """ACTION items included; ACCEPT items excluded; gate = PASS."""
        result = build_delivery_control_plan(
            make_ctq_nodes(), make_fmea_results(), make_ctq_mapping()
        )
        assert result.gate == "PASS"
        assert len(result.control_plan) == 1
        assert result.control_plan[0].process_step == "No operator buy-in"
        assert result.control_plan[0].ctq_name == "Training completion rate"
        assert result.control_plan[0].is_placeholder is False

    def test_two_action_items_same_ctq_produce_two_rows(self):
        """Each FMEA item gets its own row — no deduplication."""
        nodes = [CTQNode("X", "CTQ A", "% units", 80, 100)]
        fmea = [
            {"mode": "Risk A", "severity": 8, "occurrence": 5, "detection": 4,
             "rpn": 160, "classification": "ACTION", "action": "Mitigate"},
            {"mode": "Risk B", "severity": 8, "occurrence": 5, "detection": 4,
             "rpn": 160, "classification": "ACTION", "action": "Mitigate"},
        ]
        mapping = {"Risk A": "CTQ A", "Risk B": "CTQ A"}
        result = build_delivery_control_plan(nodes, fmea, mapping)
        assert len(result.control_plan) == 2
        assert result.control_plan[0].ctq_name == "CTQ A"
        assert result.control_plan[1].ctq_name == "CTQ A"

    def test_accept_items_are_excluded(self):
        """ACCEPT items do not appear in the control plan."""
        nodes = [CTQNode("X", "CTQ A", "count", 0, 10)]
        fmea = [
            {"mode": "Low risk", "severity": 3, "occurrence": 3, "detection": 3,
             "rpn": 27, "classification": "ACCEPT", "action": "Accept – monitor"},
        ]
        result = build_delivery_control_plan(nodes, fmea, {})
        assert result.control_plan == []
        assert result.gate == "PASS"

    def test_empty_ctq_list_raises_g1_error(self):
        """G1: empty CTQ list → ValueError before any plan is built."""
        with pytest.raises(ValueError, match="G1"):
            build_delivery_control_plan([], make_fmea_results(), make_ctq_mapping())

    def test_andon_item_included_in_plan(self):
        """ANDON items are included (blocking was P3's job; control plan tracks them)."""
        nodes = [CTQNode("X", "CTQ A", "count", 0, 5)]
        mapping = {"Critical system failure": "CTQ A"}
        result = build_delivery_control_plan(nodes, make_andon_fmea(), mapping)
        assert len(result.control_plan) == 1
        assert result.control_plan[0].classification == "ANDON"
        assert result.control_plan[0].is_andon is True


# ── Feature 2: Placeholder mode ───────────────────────────────────────────

class TestPlaceholderMode:

    def test_no_mapping_produces_placeholder_rows_for_all_ctqs(self):
        """ctq_mapping=None → one placeholder row per CTQ; gate = PASS."""
        result = build_delivery_control_plan(make_ctq_nodes(), [], None)
        assert result.gate == "PASS"
        assert len(result.control_plan) == 3
        assert all(item.is_placeholder for item in result.control_plan)

    def test_placeholder_rows_use_ctq_name_as_identifier(self):
        """Placeholder rows carry the CTQ name from the node."""
        result = build_delivery_control_plan(make_ctq_nodes(), [], None)
        names = [item.ctq_name for item in result.control_plan]
        assert "On-time delivery rate" in names
        assert "Training completion rate" in names

    def test_g3_warning_added_in_placeholder_mode(self):
        """G3 warning is included when no mapping provided."""
        result = build_delivery_control_plan(make_ctq_nodes(), [], None)
        assert any("G3" in w for w in result.warnings)

    def test_andon_fmea_in_placeholder_mode_sets_daily_frequency(self):
        """ANDON FMEA item in placeholder mode → first CTQ row gets Daily frequency."""
        nodes = [CTQNode("X", "CTQ A", "count", 0, 5)]
        result = build_delivery_control_plan(nodes, make_andon_fmea(), None)
        assert result.control_plan[0].frequency == DEFAULT_FREQUENCY_ANDON
        assert result.control_plan[0].is_andon is True

    def test_placeholder_mode_with_no_fmea_uses_default_frequency(self):
        """No FMEA results in placeholder mode → DEFAULT_FREQUENCY_PLACEHOLDER."""
        nodes = [CTQNode("X", "CTQ A", "count", 0, 5)]
        result = build_delivery_control_plan(nodes, [], None)
        assert result.control_plan[0].frequency == DEFAULT_FREQUENCY_PLACEHOLDER

    def test_empty_ctq_list_in_placeholder_mode_raises_g1(self):
        """G1 fires before placeholder logic — no CTQs means no plan."""
        with pytest.raises(ValueError, match="G1"):
            build_delivery_control_plan([], [], None)


# ── Feature 3: Gate enforcement ───────────────────────────────────────────

class TestGateEnforcement:

    def test_g3_passes_when_all_action_items_mapped(self):
        """All ACTION items in ctq_mapping → no G3 error."""
        result = build_delivery_control_plan(
            make_ctq_nodes(), make_fmea_results(), make_ctq_mapping()
        )
        assert result.gate == "PASS"

    def test_g3_raises_for_unmapped_action_item(self):
        """G3: ACTION item not in ctq_mapping → ValueError."""
        with pytest.raises(ValueError, match="G3"):
            build_delivery_control_plan(make_ctq_nodes(), make_fmea_results(), {})

    def test_g4_raises_for_unknown_ctq_name_in_mapping(self):
        """G4: ctq_mapping value not in ctq_nodes → ValueError."""
        bad_mapping = {"No operator buy-in": "UNKNOWN CTQ"}
        with pytest.raises(ValueError, match="G4"):
            build_delivery_control_plan(make_ctq_nodes(), make_fmea_results(), bad_mapping)

    def test_g2_missing_lsl_adds_warning_not_error(self):
        """G2: CTQ missing LSL → warning added; gate still PASS."""
        nodes = [CTQNode("X", "CTQ A", "count", None, 10)]
        fmea = [
            {"mode": "Risk A", "severity": 7, "occurrence": 5, "detection": 4,
             "rpn": 140, "classification": "ACCEPT", "action": "Accept"},
        ]
        result = build_delivery_control_plan(nodes, fmea, {})
        assert result.gate == "PASS"
        assert any("G2" in w and "LSL" in w for w in result.warnings)

    def test_g2_missing_usl_adds_warning_not_error(self):
        """G2: CTQ missing USL → warning added; gate still PASS."""
        nodes = [CTQNode("X", "CTQ A", "count", 0, None)]
        fmea = []
        result = build_delivery_control_plan(nodes, fmea, {})
        assert result.gate == "PASS"
        assert any("G2" in w and "USL" in w for w in result.warnings)


# ── Feature 4: CTQ coverage validation ────────────────────────────────────

class TestCTQCoverageValidation:

    def test_all_ctqs_referenced_no_orphans(self):
        """Single CTQ mapped → no orphan warning."""
        nodes = [CTQNode("X", "CTQ A", "% units", 80, 100)]
        fmea = [
            {"mode": "Risk A", "severity": 7, "occurrence": 5, "detection": 5,
             "rpn": 175, "classification": "ACTION", "action": "Mitigate"},
        ]
        mapping = {"Risk A": "CTQ A"}
        result = build_delivery_control_plan(nodes, fmea, mapping)
        assert result.orphan_ctqs == []
        assert not any("Orphan" in w for w in result.warnings)

    def test_unreferenced_ctq_in_strict_mode_adds_orphan_warning(self):
        """3 CTQs but only 1 mapped → 2 orphans; gate still PASS."""
        result = build_delivery_control_plan(
            make_ctq_nodes(), make_fmea_results(), make_ctq_mapping()
        )
        assert len(result.orphan_ctqs) == 2
        assert any("Orphan CTQs" in w for w in result.warnings)
        assert result.gate == "PASS"

    def test_orphan_check_skipped_in_placeholder_mode(self):
        """ctq_mapping=None → orphan_ctqs = [] (not meaningful in placeholder mode)."""
        result = build_delivery_control_plan(make_ctq_nodes(), [], None)
        assert result.orphan_ctqs == []

    def test_validate_ctq_coverage_standalone(self):
        """validate_ctq_coverage() utility returns unreferenced CTQ names."""
        from src.pillar4.control_plan import ControlPlanItem, _format_specification
        nodes = make_ctq_nodes()
        item = ControlPlanItem(
            process_step="Step 1",
            ctq_name="Training completion rate",
            unit="% operators trained",
            lsl=80, usl=100,
            specification="LSL: 80 / USL: 100 % operators trained",
            measurement_method="Weekly % calculation",
            sample_size="100% of units",
            frequency="Weekly",
            control_method="SPC chart with control limits",
            owner="Operations Manager",
            reaction_plan="Mitigate",
            is_placeholder=False,
        )
        orphans = validate_ctq_coverage(nodes, [item])
        assert "On-time delivery rate" in orphans
        assert "Report acceptance rate" in orphans
        assert "Training completion rate" not in orphans


# ── Feature 5: Measurement and frequency defaults ─────────────────────────

class TestMeasurementAndFrequencyDefaults:

    def _single_action_plan(self, unit, mode="Risk A", rpn=175, classification="ACTION",
                             measurement_override=None, owner_override=None):
        nodes = [CTQNode("X", "CTQ A", unit, 80, 100)]
        fmea = [{"mode": mode, "severity": 7, "occurrence": 5, "detection": 5,
                 "rpn": rpn, "classification": classification, "action": "Mitigate"}]
        mapping = {mode: "CTQ A"}
        return build_delivery_control_plan(
            nodes, fmea, mapping,
            measurement_overrides={mode: measurement_override} if measurement_override else None,
            owner_overrides={mode: owner_override} if owner_override else None,
        )

    def test_percentage_unit_derives_weekly_calculation(self):
        result = self._single_action_plan("% deliverables on time")
        assert result.control_plan[0].measurement_method == "Weekly % calculation"

    def test_rate_unit_derives_weekly_calculation(self):
        result = self._single_action_plan("defect rate per 1000 units")
        assert result.control_plan[0].measurement_method == "Weekly % calculation"

    def test_days_unit_derives_time_tracking(self):
        result = self._single_action_plan("days to close")
        assert result.control_plan[0].measurement_method == "Time tracking log"

    def test_hours_unit_derives_time_tracking(self):
        result = self._single_action_plan("hours per task")
        assert result.control_plan[0].measurement_method == "Time tracking log"

    def test_other_unit_uses_default_method(self):
        result = self._single_action_plan("count of defects")
        assert result.control_plan[0].measurement_method == "Manual inspection / SPC"

    def test_measurement_override_takes_precedence(self):
        result = self._single_action_plan("% units", measurement_override="Automated dashboard")
        assert result.control_plan[0].measurement_method == "Automated dashboard"

    def test_andon_item_gets_daily_frequency(self):
        result = self._single_action_plan("count", rpn=300, classification="ANDON")
        assert result.control_plan[0].frequency == DEFAULT_FREQUENCY_ANDON

    def test_action_item_gets_weekly_frequency(self):
        result = self._single_action_plan("count", rpn=175, classification="ACTION")
        assert result.control_plan[0].frequency == DEFAULT_FREQUENCY_ACTION

    def test_andon_rpn_threshold_sets_is_andon_flag(self):
        """RPN == RPN_ANDON_THRESHOLD (300) → is_andon = True."""
        result = self._single_action_plan("count", rpn=RPN_ANDON_THRESHOLD, classification="ANDON")
        assert result.control_plan[0].is_andon is True
        assert len(result.andon_flags) == 1

    def test_below_andon_threshold_is_not_andon(self):
        """RPN 299 → is_andon = False."""
        result = self._single_action_plan("count", rpn=299, classification="ACTION")
        assert result.control_plan[0].is_andon is False
        assert result.andon_flags == []

    def test_owner_override_replaces_default(self):
        result = self._single_action_plan("count", owner_override="Lead Consultant")
        assert result.control_plan[0].owner == "Lead Consultant"

    def test_no_owner_override_uses_default_owner(self):
        result = self._single_action_plan("count")
        assert result.control_plan[0].owner == DEFAULT_OWNER

    def test_include_reaction_plan_false_omits_reaction(self):
        nodes = [CTQNode("X", "CTQ A", "count", 0, 5)]
        fmea = [{"mode": "Risk A", "severity": 7, "occurrence": 5, "detection": 5,
                 "rpn": 175, "classification": "ACTION", "action": "Mitigate"}]
        result = build_delivery_control_plan(nodes, fmea, {"Risk A": "CTQ A"}, include_reaction_plan=False)
        assert result.control_plan[0].reaction_plan == ""

    def test_include_owner_false_omits_owner(self):
        nodes = [CTQNode("X", "CTQ A", "count", 0, 5)]
        fmea = [{"mode": "Risk A", "severity": 7, "occurrence": 5, "detection": 5,
                 "rpn": 175, "classification": "ACTION", "action": "Mitigate"}]
        result = build_delivery_control_plan(nodes, fmea, {"Risk A": "CTQ A"}, include_owner=False)
        assert result.control_plan[0].owner == ""


# ── Feature 6: Render output ──────────────────────────────────────────────

class TestRenderOutput:

    def _build_clean_result(self):
        nodes = [CTQNode("X", "CTQ A", "% units", 80, 100)]
        fmea = [{"mode": "Risk A", "severity": 7, "occurrence": 5, "detection": 5,
                 "rpn": 175, "classification": "ACTION", "action": "Mitigate"}]
        mapping = {"Risk A": "CTQ A"}
        return build_delivery_control_plan(nodes, fmea, mapping)

    def test_render_contains_title_and_table_headers(self):
        result = self._build_clean_result()
        md = render_control_plan_md(result, engagement_name="Acme Aerospace")
        assert "# Control Plan – Acme Aerospace" in md
        assert "Process Step" in md
        assert "CTQ Characteristic" in md
        assert "Reaction Plan" in md

    def test_render_contains_sign_off_section(self):
        result = self._build_clean_result()
        md = render_control_plan_md(result)
        assert "## Sign-off" in md
        assert "CTQ tree reviewed" in md
        assert "FMEA reviewed" in md

    def test_render_includes_andon_warnings_section_when_flags_present(self):
        nodes = [CTQNode("X", "CTQ A", "count", 0, 5)]
        mapping = {"Critical system failure": "CTQ A"}
        result = build_delivery_control_plan(nodes, make_andon_fmea(), mapping)
        md = render_control_plan_md(result)
        assert "## ANDON / Warnings" in md
        assert "RPN" in md

    def test_render_omits_warnings_section_when_no_flags(self):
        result = self._build_clean_result()
        md = render_control_plan_md(result)
        assert "## ANDON / Warnings" not in md

    def test_render_includes_date_when_provided(self):
        result = self._build_clean_result()
        md = render_control_plan_md(result, date="2026-06-17")
        assert "**Date:** 2026-06-17" in md

    def test_render_uses_client_name_in_title_when_provided(self):
        result = self._build_clean_result()
        md = render_control_plan_md(result, client_name="Rolls-Royce")
        assert "# Control Plan – Rolls-Royce" in md
        assert "approved by Rolls-Royce" in md
