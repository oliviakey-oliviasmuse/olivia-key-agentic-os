# Pillar 3 Agent Overview
# Sales & Client Acquisition

## Why Pillar 3 Exists

Pillar 2 builds the audience. Pillar 3 converts it. Without a structured qualification system, sales conversations happen at random — with the wrong prospects, at the wrong time, creating high CAC and low close rates.

Pillar 3 applies LSS and Daniel Priestley's scorecard marketing methodology to the qualification process. Every prospect is assessed against objective criteria before any live sales time is invested. The scorecard positions expertise (help first), then moves to a conversation once fit is confirmed.

---

## The Agent — Scorecard Generator & Analyser

**Purpose:** Generate a personalised diagnostic scorecard for a prospect, collect their responses, calculate a score, and output an objective PROCEED / DEFER / REJECT recommendation.

**Input:** Prospect name, company, industry, role, pain area, scorecard type
**Output:** Copyable markdown scorecard (Phase 1); scored result with recommendation and log entry (Phase 2)

**Three scorecard types:**
- `CoPQ_Health` — tracks internal/external failure costs, measurement maturity (default)
- `Hidden_Factory` — tracks waste visibility, non-value-added time, rework exposure
- `Ops_Maturity` — tracks process documentation, CI programme, measurement system validation

**Recommendation thresholds (configurable):**
| Score | Outcome | Meaning |
|-------|---------|---------|
| ≥ 18 | PROCEED | Strong pain signal + measurement awareness → Discovery Call |
| 12–17 | DEFER | Pain exists but infrastructure underdeveloped → gather more data |
| < 12 | REJECT | Low pain signal or no measurement system → not a current fit |

**Quality gates:** G1 (5–10 questions, 0–3 scale), G2 (industry-specific questions), G3 (arithmetic verified), G4 (recommendation matches threshold)

**Defect codes:** S1 (no response), S2 (false positive — passed but didn't convert), S3 (false negative — failed but later converted)

**Learning loop:** 3 × S2 or S3 → threshold calibration recommendation

---

## How Pillar 3 Connects to Other Pillars

**P2 → P3:** Pillar 2 content (especially BOFU Hero posts) generates qualified warm leads who arrive with context. Scorecard score is higher for warm leads than cold outreach.

**P3 → P1:** A PROCEED scorecard result triggers a Discovery Call, which uses the Pillar 1 CoPQ pricing tool to generate a value-based proposal.

**P3 → P4 (future):** Discovery Call notes and scored responses feed into the proposal and engagement setup.

---

## Outreach Log

Every scored prospect is appended to `outreach_log.md` at the project root. Fields: prospect name, company, date, scorecard type, score, recommendation, notes. Append only — never edit previous entries.

The outreach log is the evidence base for threshold calibration (S2/S3 review) and pipeline reporting.

---

## What This Agent Does NOT Do

- Does not conduct the Discovery Call (that is a human-led conversation informed by Pillar 1)
- Does not send messages directly — outputs copyable content for the user to send
- Does not track CRM pipeline beyond the outreach log (future integration)

---

## Agent 2 — Discovery Call Gatekeeper

**Purpose:** Score a prospect against the ICP rubric (maximum 25 points) and output a go/no-go recommendation for the Discovery Call. Triggered by a PROCEED result from Agent 1, or run independently on LinkedIn/company data before the scorecard is sent.

**Input:** Any combination of job title, company name, industry, employee count, annual revenue, pain description, budget authority notes, completed Agent 1 scorecard, `warm_lead` flag.

**Output:** Scored ICP report (XX/25), PROCEED / DEFER / REJECT recommendation, estimated CoPQ range, missing fields list, justification per category, next action.

**ICP rubric (5 categories × 5 points = 25 max):**

| Category | Max | 5-point criteria |
|----------|-----|-----------------|
| Role | 5 | VP Ops / COO / Plant Manager |
| Company size | 5 | 1,000+ employees |
| Industry | 5 | Capital-intensive: aerospace, automotive, logistics, heavy manufacturing, defence, energy, mining, rail |
| Pain awareness | 5 | Mentions CoPQ, hidden factory, rework, scrap, downtime, or variation |
| Budget authority | 5 | Has budget sign-off or P&L ownership |

**Recommendation thresholds:**

| Lead type | PROCEED | DEFER | REJECT |
|-----------|---------|-------|--------|
| Cold | ≥ 18 | 8–17 | < 8 |
| Warm (DM / download / call request / CoPQ estimate) | ≥ 14 | 8–13 | < 8 |

**Agent 1 bridge:** If a completed scorecard is available, its total is mapped to the ICP scale: `round(scorecard_total × 1.04)`. This converts Agent 1's /24 scale to /25.

**CoPQ estimate:** Revenue × 0.15, ±20% range. If revenue unknown, flagged as "ask on call."

**G1 gate:** Fewer than 3 ICP attributes populated → stop, request more data.

**Defect codes:** S1 (false positive — PROCEED but no opportunity), S2 (false negative — REJECT but later converts), S3 (CoPQ estimate off by >50%). 3× S1 or S2 → ANDON: rubric recalibration required.

**Code location:** `src/pillar3/gatekeeper.py`
**System prompt:** `src/system_prompts/agent_gatekeeper.md` — v1.0
**Test coverage:** `evals/level1/test_gatekeeper.py` — 73 tests, all passing
