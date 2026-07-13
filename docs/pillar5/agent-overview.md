# Agent Overview — Pillar 5: Operations & Governance

## Purpose
Pillar 5 operationalises the "third time" rule: any repeatable process executed three times without a written SOP is a governance failure. Agent 0 generates, versions, and stores SOPs before that failure occurs.

## Agent Map

| Agent | Name | File | Tests |
|-------|------|------|-------|
| 0 | SOP Writer | sop_writer.py / sop_writer_generator.py | ✓ |

## Agent 0 — SOP Writer

**Entry points:**
- `create_sop(...)` — create SOP from dict inputs
- `generate_sop_report(sop, library_path)` — render markdown + append to Framework Library

**Key logic:**
- G1–G5 gates enforce all required fields before any SOP is generated
- ANDON trigger fires when trigger_count ≥ 3 (warning prepended to output, generation continues)
- `purpose` auto-derived from `description` when omitted
- `review_date` defaults to +6 months from creation
- `format_sop_markdown()` produces consistent structure: Purpose → Scope → Inputs → Outputs → Steps → Quality Gates → Defect Codes → Change Log → Sign-off
- `generate_sop_filename()` produces filesystem-safe filenames
- `increment_version()` increments minor version (1.0 → 1.1)

## KPIs This System Supports
| KPI | Target | How Tracked |
|-----|--------|-------------|
| SOPs in Framework Library | 100% of repeatable processes | Framework Library append count |
| SOP coverage before 3rd execution | 100% | trigger_count ANDON alerts |
| SOP review compliance | 100% within review_date | Change Log + sign-off |
