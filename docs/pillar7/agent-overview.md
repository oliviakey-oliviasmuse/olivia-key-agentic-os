# Agent Overview — Pillar 7: Knowledge, Systems & Improvement

## Purpose
Capture and institutionalise learning from every engagement. PRINCE2 mandates that lessons are applied — not just documented. This agent enforces that mandate deterministically.

## Agent 0: Lessons Report Generator

**Role:** Generate a PRINCE2 Lessons Report within 5 days of engagement close. Every report must produce a corrective action. Every corrective action must be linked to an SOP update or explicit decision not to update.

**Non-negotiable constraints:**
- Report must be generated within 5 working days of close_date (L1 defect if not)
- Root cause must be provided — symptom-level analysis is not accepted (G6)
- If sop_update_required=True, description of the SOP update is mandatory

**Inputs:**
| Field | Type | Required |
|-------|------|----------|
| engagement_name | str | Yes (G1) |
| client_name | str | Yes (G2) |
| close_date | str (YYYY-MM-DD) | Yes (G3) |
| what_worked | list[str] ≥ 1 | Yes (G4) |
| what_didnt | list[str] ≥ 1 | Yes (G5) |
| root_cause | str | Yes (G6) |
| corrective_action | str | Yes (G7) |
| sop_update_required | bool | Yes |
| sop_update_description | str | Required if sop_update_required=True |

**Outputs:**
- PRINCE2 Lessons Report (markdown)
- Lessons Log entry (plain text, timestamped, append-only)

**Defect Codes:**
| Code | Description |
|------|-------------|
| L1 | Report not generated within 5 days → lost learning |
| L2 | SOP update required but not executed → repeated mistake |
| L3 | Root cause not identified → symptom treated, not cause |
