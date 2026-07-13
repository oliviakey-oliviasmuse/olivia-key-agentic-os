# Olivia Key — Pillar 1 Agentic System
# Agent Overview

## What This Agent Does

The Pillar 1 Agentic System automates the three core workflows of Offer Design & Productization:

1. **Core Service Design** — Guides the user through building a SIPOC and CTQ tree for a new engagement. Enforces the gate: no CTQ tree without a complete SIPOC first.
2. **PPD Generator** — Produces a PRINCE2-compliant Project Product Description for each deliverable. Quality-checks the PPD itself before returning it. Blocks any output with subjective quality criteria.
3. **CoPQ Pricing Calculator** — Takes prospect cost inputs across four categories, calculates total annual CoPQ, and returns a value-based pricing recommendation at 10–20% of recovery. Hard floor: £5,000/month.

## Why This Pillar First

Pillar 1 is the foundation everything else depends on. The CTQ vocabulary feeds content (Pillar 3). The PPDs define what is being sold (Pillar 4). The CoPQ calculation is used in every discovery call and proposal (Pillar 4). Without Pillar 1 codified, no other pillar has a consistent standard to execute against.

## Source Blueprint

Master Operating Blueprint — Pillar 1: Offer Design & Productization
- Objectives 1–3 (Core Service Design, Deliverables Standardization, Value-Based Pricing)
- Tactics 1–3 (SIPOC + CTQ, PPD, CoPQ pricing)
- KPIs: First-Time Acceptance Rate, AOV, % Revenue from Productised IP
- The P2 Loop: Service designed to CTQ → delivered to PPD standard → accepted first time → case study → refined → repeat

## Methodology Embedded

| Framework | Where Applied |
|-----------|--------------|
| LSS SIPOC | Core service delivery chain mapping |
| LSS CTQ Tree | Translating enterprise needs to measurable requirements with LSL/USL |
| PRINCE2 PPD | Six-field deliverable specification, quality-checked before production |
| CoPQ (4-category) | Internal failure + external failure + appraisal + prevention costs |
| FMEA (via Appendix B) | RPN scoring on any major deliverable: Severity × Occurrence × Detection |

## Agent Inputs

- Service name and client industry context
- Engagement scope description
- Prospect cost data (for CoPQ: 4 cost categories)
- Deliverable list (for PPD generation)

## Agent Outputs

- Completed SIPOC (5 columns, no blanks)
- CTQ tree with LSL/USL for every node
- PPDs for each deliverable (6 fields, quality-checked, binary criteria only)
- CoPQ calculation with itemised breakdown
- Pricing recommendation (10–20% of CoPQ recovery, ≥£5k/month floor)
- ROI narrative for proposal use

## Stage Gates (Non-Negotiable)

1. No CTQ tree without complete SIPOC
2. No deliverable work without countersigned PPD
3. No pricing recommendation below £5,000/month
4. No ROI narrative without a numeric CoPQ anchor

## Trace Logging

Every agent interaction logs to `/evals/traces/` as a JSON record:
```json
{
  "timestamp": "ISO-8601",
  "feature": "sipoc|ctq|ppd|copq",
  "input": {},
  "output": {},
  "quality_check_passed": true,
  "gate_triggered": false,
  "gate_reason": null
}
```
