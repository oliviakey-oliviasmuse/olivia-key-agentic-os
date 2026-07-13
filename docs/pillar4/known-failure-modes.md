# Known Failure Modes — Pillar 4

## FMEA — Agent 1: Delivery Control Plan Generator

| Code | Failure Mode | Severity (1-10) | Occurrence (1-10) | Detection (1-10) | RPN | Status |
|------|--------------|-----------------|-------------------|------------------|-----|--------|
| FM-01 | Control Plan built without explicit CTQ mapping — placeholder rows delivered as final output | 8 | 5 | 4 | 160 | Mitigated: G3 warning flags placeholder rows |
| FM-02 | CTQ missing LSL/USL delivered to client — control limit undefined | 9 | 4 | 3 | 108 | Mitigated: G2 soft warning flags missing specs |
| FM-03 | ANDON item in control plan not resolved before handover — client takes ownership of an unmitigated risk | 9 | 3 | 5 | 135 | Open: sign-off checklist includes ANDON review; no automated block yet |
| FM-04 | Orphan CTQ (no FMEA-linked control point) missed at handover | 7 | 4 | 4 | 112 | Mitigated: orphan_ctqs returned in result; warning added |
| FM-05 | control_plan_generator.py (dict API) used in production instead of control_plan.py — gates bypassed | 8 | 3 | 6 | 144 | Open: LLM wrapper should call control_plan.py internally in v1.1 |

## RPN Summary

| Priority | FM | RPN | Action |
|----------|----|-----|--------|
| 1 | FM-01 | 160 | G3 warning in place; escalate to hard error in v1.1 if placeholder delivered to client |
| 2 | FM-05 | 144 | Refactor wrapper to call deterministic layer; Decision-02 |
| 3 | FM-03 | 135 | Add ANDON gate to sign-off flow in Agent 2 (FTA Tracker) |
| 4 | FM-04 | 112 | orphan_ctqs surfaced in result; no further action |
| 5 | FM-02 | 108 | G2 soft gate in place; acceptable |
