# Pillar 2 Agent Overview
# Marketing & Demand Generation

## Why Pillar 2 Exists

Pillar 1 (Offer Design) produces a measurable, priced service. Pillar 2 builds the audience that makes selling that service inevitable. Without a structured, gate-controlled content system, content becomes a vanity exercise: time spent on posts that don't move commercial outcomes.

Pillar 2 applies LSS Sustain and CIM methodology to content production — the same rigour sold to clients, applied internally.

---

## The Four Agents

### Agent 1 — Content Quality Gate
**Purpose:** Pre-publication audit. Prevents substandard content reaching the audience.
**Input:** Draft content + commercial objective + tier
**Output:** PASS / FAIL / ANDON STOP verdict with content ID, defect codes, corrective actions
**Post-publication loop:** 14-day feedback → predicted vs actual comparison → M9 if variance >50%
**Learning loop:** 3 same-code defects → root cause analysis; 6 cumulative → scrap trigger

**Key enforcement:**
- G12 (hype words), G13 (citations), G14 (E-E-A-T) are ANDON gates — immediate stop, no override
- G15 (schema readiness) is conditional on `include_geo_check=true`
- G16 (commercial CTA) enforces objective alignment — fail = M10

### Agent 2 — Market Monitor
**Purpose:** Weekly intelligence. Identifies what the ICP is paying attention to and scores it for commercial potential.
**Input:** Keywords, platforms, competitor handles, first-party data
**Output:** Weekly report with platform analysis, sentiment, competitor watch, AI visibility, ranked actionable insights
**Accuracy loop:** Logs whether trends led to commercial results
**False signal detection:** 3 zero-result trends from same source → deprecation warning
**Scrap trigger:** 4 consecutive weeks of ≥80% synthetic engagement → CRITICAL

### Agent 3 — Content Hypothesis Generator
**Purpose:** Generates 3–5 ranked content hypotheses per week, derived from Agent 2's output.
**Input:** Market Monitor report
**Output:** Ranked hypotheses (HYP-YYYYMMDD-NN) with dominant factor, predicted engagement, commercial potential
**Weight adjustment:** After 3 H6 defects, recalculates ranking weights
**Scrap trigger:** 3 consecutive rank-1 failures → recommend scrapping hypothesis model

### Agent 4 — Strategy Optimizer
**Purpose:** Monthly internal performance review. Analyses GA4, CRM, LinkedIn, and email data to assess whether published content is producing commercial results and where to reallocate effort.
**Input:** Daily data files from `data/feeds/YYYY-MM-DD.json` (GA4 automated; LinkedIn manual weekly export)
**Output:** KPI dashboard (GREEN/AMBER/RED per metric), ranked recommendations with data rationale, linear trend forecast, attribution summary, next-period focus statement
**ANDON conditions:** Efficiency Crisis (CAC +20% + conversion -10% simultaneously), Negative ROI (two consecutive periods), Data Gap (critical source >7 days stale)
**Defect codes:** D1 (recommendation produced no improvement), D2 (missed trend causing performance drop), D3 (attribution misattribution), D4 (forecast error >30% two consecutive periods)

**Why Agent 4 is separate from Agent 2:**
Agent 2 uses external data at weekly cadence to answer "what is the market paying attention to?" Agent 4 uses internal performance data at monthly cadence to answer "is what we're producing actually working?" Different data, different cadence, different decisions. See `docs/build-decisions.md` — Decision 5.

---

## The Closed Iteration Loop

```
Agent 2 (external trend intelligence — weekly)
  ↓ ranked signals (score ≥7)
Agent 3 (hypothesis generation — weekly)
  ↓ HYP IDs
User (content creation + Agent 1 gate check + publish)
  ↓ 14 days
User (feeds back actual ER + commercial result to Agents 1 and 3)
  ↓
Agent 1: predicted vs actual → M9 if >50% variance → gate change after 3 occurrences
Agent 3: rank-1 failure → H6 → weight adjustment after 3 → scrap after 3 consecutive
Agent 2: trend logged → false signal after 3 non-commercial → source deprecated
  ↓
LESSONS_LOG.md updated

Agent 4 (internal performance review — monthly)
  ↓ reads data/feeds/ accumulated daily data
Produces: KPI dashboard + recommendations + attribution + next-period focus
  ↓
User acts on recommendations → logs outcome in data/feeds/_meta (closes D1 loop)
```

---

## Programmatic vs LLM Gates

| Gate | Enforced programmatically? | Notes |
|------|---------------------------|-------|
| G2 (CoPQ term) | Yes | Word list in content_gate.py |
| G5 (word count) | Yes | ±20% tolerance per tier |
| G10 (vanity metrics) | Yes | Phrase-matching |
| G12 (hype words) | Yes | Word-boundary regex — ANDON gate |
| G13 (source verification) | Yes — partial | Named source extraction + verified_sources check; LLM handles E-E-A-T component (G14) |
| G15 (schema) | Yes (conditional) | Only when include_geo_check=True |
| G16 (commercial CTA) | Yes | Phrase-matching per objective |
| G17 (funnel alignment) | Yes | Two hard rules: TOFU+BOFU block; BOFU without first-party block |
| G1, G3, G4, G6, G7, G8, G9, G11, G14 | LLM-evaluated | In system prompt; G14 is ANDON gate |

---

## Feeds and Dependencies

**P1 → P2:** CTQ vocabulary (LSL/USL, CoPQ language) from Pillar 1 is the subject matter of Hygiene-tier content. The service design from P1 is the subject of Hero-tier content.

**P2 → P3 (Sales):** Content-Attributed Qualified Enquiries (P2 KPI3) are the input to P3's pipeline.

**P2 → P8 (Knowledge):** Every engagement triggered by content becomes a case study and lesson.
