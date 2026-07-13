# Known Failure Modes — Pillar 2
# FMEA: Severity (S) × Occurrence (O) × Detectability (D) = RPN

| ID | Failure Mode | Effect | S | O | D | RPN | Mitigation |
|----|-------------|--------|---|---|---|-----|-----------|
| FM-01 | Content passes all gates but produces zero commercial result | Time wasted; no pipeline contribution | 8 | 4 | 5 | 160 | Post-publication M9 loop; 14-day review mandatory |
| FM-02 | Learning loop not closed — user forgets to feed back results | Weights never adjust; model drifts | 9 | 5 | 4 | 180 | Weekly reminder in Agent 3 output; LESSONS_LOG.md reviewed each Monday |
| FM-03 | Market Monitor false positives — trends that don't convert | Wasted content production effort | 6 | 4 | 3 | 72 | False signal detection at 3 occurrences; source deprecation |
| FM-04 | G12 ANDON bypass attempted (hype word removed without improving substance) | Diluted brand voice; credibility erosion | 9 | 2 | 6 | 108 | G12 is code-enforced, not LLM-evaluated — cannot be bypassed |
| FM-05 | Hypothesis ranking model calibrated on too few data points | Premature weight adjustment misfires | 5 | 3 | 5 | 75 | Adjustment requires 3 H6 failures — not triggered earlier |
| FM-06 | G15 schema gate creates format rigidity (every post has H2 headers) | Content feels mechanical; ER drops | 4 | 3 | 6 | 72 | G15 is conditional — only enforced when `include_geo_check=true` |
| FM-07 | Synthetic engagement inflation inflates ER metrics | False positive on platform viability | 7 | 4 | 4 | 112 | SyntheticEngagementTracker scrap trigger at 4 consecutive weeks |
| FM-08 | Commercial objective not specified — content gets 'brand_awareness' by default | CTA missing; no pipeline contribution | 8 | 3 | 7 | 168 | G16 enforced per objective; brand_awareness is an explicit choice, not a default escape |

| FM-09 | Data feed stale — GA4 credentials expire or LinkedIn CSV not refreshed → Agent 4 runs on outdated data | Wrong recommendations from lagging signals | 7 | 4 | 4 | 112 | `check_andon_data_gap()` fires after 7 days; `ingest_daily.py` prints warning if <3 sources collected |
| FM-10 | Attribution distorted by single-period spike (e.g., viral post inflates LinkedIn share) | Budget reallocated to channel that appeared to outperform | 6 | 4 | 4 | 96 | Flag when one channel >60% attribution in a single period — confirm trend over 3+ periods before reallocation |
| FM-11 | KPI formula drift — CRM or analytics tool changes how CAC is calculated silently | Period-over-period comparisons become meaningless | 7 | 3 | 6 | 126 | Document formula versions in `data/feeds/_meta.notes`; Agent 4 G2 gate enforces consistent formulas |
| FM-12 | Agent 4 recommendations not closed — no feedback on whether actions were taken | D1 defects accumulate silently; model cannot learn | 8 | 5 | 4 | 160 | Monthly review mandatory; log implementation status per recommendation in `data/feeds/` meta field |

---

## Highest Priority Failure Modes (RPN ≥ 150)

1. **FM-02** (RPN 180): Learning loop not closed. Highest risk — structural. Mitigation: make feedback review a Monday workflow item.
2. **FM-08** (RPN 168): Commercial objective not specified. Mitigation: G16 enforcement + no default escape to brand_awareness.
3. **FM-01** (RPN 160): Content passes gates but fails commercially. Mitigation: mandatory 14-day post-publication review via Agent 1 Step 4.
4. **FM-12** (RPN 160): Agent 4 recommendations not acted on or closed. Mitigation: monthly review mandatory; log implementation status per recommendation.

## Full RPN Summary (all 4 agents)

| FM | Agent | Description | RPN |
|----|-------|-------------|-----|
| FM-02 | Agent 1 | Learning loop not closed | 180 |
| FM-08 | Agent 1 | Commercial objective unspecified | 168 |
| FM-01 | Agent 1 | Content passes gates but zero commercial result | 160 |
| FM-12 | Agent 4 | Recommendations not closed — D1 accumulates silently | 160 |
| FM-07 | Agent 2 | Synthetic engagement inflation | 112 |
| FM-11 | Agent 4 | KPI formula drift between periods | 126 |
| FM-04 | Agent 1 | G12 bypass attempted | 108 |
| FM-09 | Agent 4 | Data feed stale | 112 |
| FM-05 | Agent 3 | Hypothesis weights calibrated too early | 75 |
| FM-03 | Agent 2 | Market Monitor false positives | 72 |
| FM-06 | Agent 1 | G15 creates format rigidity | 72 |
| FM-10 | Agent 4 | Attribution distorted by single-period spike | 96 |
