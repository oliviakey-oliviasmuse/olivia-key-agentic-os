"""
Central defect code registry — single source of truth for all defect codes
across the 8-pillar agentic operating system.

Before this registry existed, defect codes drifted:
    - S1 in Pillar 0 scorecard = "prospect did not return"
    - S1 in Pillar 3 gatekeeper = "false positive"
    - D1 in Pillar 0 control plan = "missing CTQ"
    - D1 in Pillar 0 drift detector = "drift not escalated"

Now every defect code is registered here, with its owner pillar and meaning.

Usage:
    from src.common.defect_codes import get_defect, list_defects, DEFECT_REGISTRY

    get_defect("S1", "pillar0")       # returns the right S1 for the pillar
    list_defects("pillar3")            # all defects owned by Pillar 3
"""
from __future__ import annotations

from typing import Optional


# ── Pillar 0: Strategy & Positioning ─────────────────────────────────────────
PILLAR0_DEFECTS: dict[str, str] = {
    "PS1": "Statement tested with fewer than 5 ICP contacts before locking",
    "PS2": "Clarity score below 80% but statement marked as locked",
    "PS3": "Subjective language present — fails objectivity gate",
    "D1": "ICP changed without logging — drift risk",
    "D2": "Voice rules not enforced — brand inconsistency",
    "D3": "Prospect outside ICP passed through — wasted sales effort",
    "R1": "Prospect scored below PROCEED threshold but discovery call booked anyway",
    "R2": "Rubric not calibrated against >=20 contacts at >=80% confidence",
    "R3": "Criteria descriptions not updated after ICP language captured from discovery",
    "M1": "Proposal fee below price floor — rejected",
    "M2": "Invoice amount below price floor — defect logged",
    "M3": "Offer sold outside menu — menu inconsistency",
    "S1": "Strategic decision made but not logged — undocumented drift",
    "S2": "Review required but not completed — stale strategy",
    "S3": "Decision reversed without log — lost context",
}


# ── Pillar 1: Offer Design & Productization ─────────────────────────────────
PILLAR1_DEFECTS: dict[str, str] = {
    # FM-01..07 documented in CHANGELOG
    "FM-01": "Incomplete SIPOC -> CTQ (RPN 135)",
    "FM-02": "Subjective language in output (RPN 192)",
    "FM-03": "Price below £5k floor (RPN 80)",
    "FM-04": "PPD missing field (RPN 96)",
    "FM-05": "Quality check skipped (RPN 120)",
    "FM-06": "ROI narrative without CoPQ (RPN 81)",
    "FM-07": "Partial CoPQ as complete (RPN 140)",
}


# ── Pillar 2: Marketing & Demand Generation ────────────────────────────────
PILLAR2_DEFECTS: dict[str, str] = {
    "M1": "Hook fails to earn click in ≤3 seconds (G1)",
    "M2": "No CoPQ/operational term present (G2)",
    "M3": "No market signal reference when VOC check enabled (G3)",
    "M4": "CTA missing, vague, or compound (G4)",
    "M5": "Length outside tier tolerance ±20% (G5)",
    "M6": "Tone inconsistent with brand adjectives (G6)",
    "M7": "Hype word detected — ANDON gate (G12)",
    "M8": "E-E-A-T signals fewer than 2 of 4 — ANDON gate (G14)",
    "M9": "Prediction error >50% variance (post-publication)",
    "M10": "Commercial CTA missing or misaligned (G16)",
    "M11": "Funnel misalignment — tier/objective or source type mismatch (G17)",
    "M12": "Voice rule violation — P0 vocabulary_avoid term detected (G18)",
    "M13": "Channel or format violation — not in P0 distribution authority (G19)",
    "D1": "Recommendation implemented — no measurable improvement within 30 days",
    "D2": "Missed significant trend that later caused performance drop",
    "D3": "Attribution model misattributed success — wrong budget allocation",
    "D4": "Forecast error >30% for two consecutive periods",
    "H1": "Hypothesis lacks market signal backing",
    "H2": "Hypothesis too generic, no ICP specificity",
    "H3": "No format suggestion provided",
    "H4": "Commercial potential not assessed",
    "H5": "Hypothesis ID not generated",
    "H6": "Prediction failure — rank-1 hypothesis produced zero commercial result",
}


# ── Pillar 3: Sales & Client Acquisition ────────────────────────────────────
# NOTE: S1/S2/S3 reused from Pillar 0 but with different meanings — see per-pillar docs.
PILLAR3_DEFECTS: dict[str, str] = {
    "S1": "Prospect did not return completed scorecard within 7 days",  # scorecard
    "S1:gatekeeper": "False positive: PROCEED but no commercial result",  # gatekeeper
    "S2:gatekeeper": "False negative: REJECT but later converted",
    "S3:gatekeeper": "CoPQ estimate error >50%",
    "S2:scorecard": "Scorecard passed (>=18) but no commercial result — false positive",
    "S3:scorecard": "Scorecard failed (<12) but later converted — false negative",
    "P1": "RPN >=300 but proposal sent — ANDON missed",
    "P2": "ROMI >0 but client rejected on price — value mis-estimated",
    "P3": "Control plan missing critical item — post-engagement",
    "C1": "Fishbone missed a major cause that later became critical",
    "C2": "CoPQ estimate >50% error vs client-validated numbers",
    "C3": "Business case PASS but deal failed to close (false positive)",
}


# ── Pillar 4: Client Delivery ──────────────────────────────────────────────
PILLAR4_DEFECTS: dict[str, str] = {
    "D1": "Control Plan missing a CTQ that later causes a defect (post-handover)",
    "D2": "Control limit (LSL/USL) wrong — false alarms or missed signals",
    "D3": "Reaction plan missing — client doesn't act on breach",
    "D4": "PID scope changed after sign-off without document update",
    "D5": "RACI missing a key role — confusion during delivery",
    "D6": "Quality standard not linked to a PPD — acceptance disputes at handover",
    "E1": "Case study published without client approval",
    "E2": "Case study outcome overstated vs client-validated number",
    "E3": "Lessons section empty — missed learning opportunity",
}


# ── Pillar 5: Operations & Governance ───────────────────────────────────────
PILLAR5_DEFECTS: dict[str, str] = {
    "C1": "Cycle time not logged — missing data",
    "C2": "Baseline not set — cannot measure improvement",
    "C3": "Reduction not tracked — missed target",
    "D1": "Defect rate >5% not investigated",
    "D2": "5 Whys not documented",
    "D3": "Corrective action not linked to SOP update",
    "IR1": "Issue escalated but no corrective action documented",
    "IR2": "Issue closed without root cause analysis",
    "IR3": "Critical issue not escalated within 24 hours",
    "S1": "SOP written but not followed",
    "S2": "SOP version not incremented correctly",
    "S3": "Owner not updated",
}


# ── Pillar 6: Finance & Commercial ──────────────────────────────────────────
PILLAR6_DEFECTS: dict[str, str] = {
    "F1": "Invoice issued but not logged — cash flow unknown",
    "F2": "Overdue invoice not chased — delayed payment",
    "F3": "Debtor days not tracked — missed early warning",
    "F4": "Budget variance >10% not investigated",
    "F5": "Unit economics not computed per channel — blind allocation",
    "F6": "Net worth snapshot not monthly — no trend visibility",
}


# ── Pillar 7: Knowledge, Systems & Improvement ─────────────────────────────
PILLAR7_DEFECTS: dict[str, str] = {
    "L1": "Report generated >5 days after close — lost learning",
    "L2": "SOP update required but not executed — repeated mistake",
    "L3": "Root cause not identified — symptom treated, not cause",
    "L4": "Framework entry duplicated — library inconsistency",
    "L5": "Pipeline status transition invalid — state machine error",
    "L6": "Product EV below threshold but not flagged for review",
}


# ── Registry ────────────────────────────────────────────────────────────────
DEFECT_REGISTRY: dict[str, dict[str, str]] = {
    "pillar0": PILLAR0_DEFECTS,
    "pillar1": PILLAR1_DEFECTS,
    "pillar2": PILLAR2_DEFECTS,
    "pillar3": PILLAR3_DEFECTS,
    "pillar4": PILLAR4_DEFECTS,
    "pillar5": PILLAR5_DEFECTS,
    "pillar6": PILLAR6_DEFECTS,
    "pillar7": PILLAR7_DEFECTS,
}


def get_defect(code: str, pillar: Optional[str] = None) -> Optional[str]:
    """
    Look up a defect code's meaning.

    If `pillar` is specified, returns the meaning for that pillar (handles
    code reuse like S1 with different meanings). If `pillar` is None,
    returns the first match across all pillars.
    """
    if pillar:
        pillar_key = pillar if pillar.startswith("pillar") else f"pillar{pillar}"
        return DEFECT_REGISTRY.get(pillar_key, {}).get(code)
    # Search across all pillars
    for pillar_defects in DEFECT_REGISTRY.values():
        if code in pillar_defects:
            return pillar_defects[code]
    return None


def list_defects(pillar: str) -> dict[str, str]:
    """Return all defect codes registered for a given pillar."""
    pillar_key = pillar if pillar.startswith("pillar") else f"pillar{pillar}"
    return dict(DEFECT_REGISTRY.get(pillar_key, {}))


def all_defect_codes() -> set[str]:
    """Return the set of all unique defect codes across all pillars."""
    codes: set[str] = set()
    for pillar_defects in DEFECT_REGISTRY.values():
        codes.update(pillar_defects.keys())
    return codes
