# Pillar 3 — Build Decisions Log
# System: Sales & Client Acquisition Agentic System
# Consultant: Olivia Key — The Systems Surgeon (oliviasmuse.com)
# Built: 2026-06-14
# Test coverage at build completion: 33 tests, 1 agent, all passing

This document records every non-obvious architectural decision made during the build of the Pillar 3 Agentic System. It exists to:
1. Explain WHY the system works the way it does
2. Provide a citable record of methodology choices and rejected alternatives
3. Enable future calibration if threshold or rubric decisions need revisiting
4. Serve as a reproducible build reference for equivalent client systems

---

## Decision 1 — Thresholds are constants, not LLM-evaluated

**Date:** 2026-06-14
**Status:** Implemented and tested

**Decision:** `THRESHOLD_PASS = 18` and `THRESHOLD_DEFER_LOW = 12` are hard-coded constants in `scorecard.py`. The recommendation (PROCEED / DEFER / REJECT) is computed deterministically from the total score. The LLM does not assess fit — it generates questions and formats output.

**Reasoning:** If the recommendation logic lives in the system prompt, the LLM can rationalise borderline scores in either direction depending on how the prospect's responses are framed. A total score of 17 is a DEFER — not a "strong 17 that feels like a PROCEED." Subjective framing in qualification is exactly what this system exists to eliminate.

The thresholds are calibrated at build time based on the ICP (capital-intensive manufacturing, VP Ops / COO / CEO level, engagement value ≥£5k/month). They should be reviewed and adjusted after 3 S2 or S3 defects — but the adjustment must be deliberate and logged, not emergent through LLM interpretation.

**Rejected approach:** Ask the LLM to assess overall fit and produce a recommendation with the total score as one input. Discarded because it reintroduces the subjectivity the scorecard is designed to remove.

**Code location:** `recommend()` in `src/pillar3/scorecard.py`
**Test coverage:** `TestRecommendation` — 7 tests covering both boundaries and all three outcomes

---

## Decision 2 — Three-tier outcome (PROCEED / DEFER / REJECT) not binary pass/fail

**Date:** 2026-06-14
**Status:** Implemented and tested

**Decision:** The scorecard produces three outcomes, not two. DEFER (12–17) is a distinct category that neither proceeds to a sales call nor closes the door.

**Reasoning:** A binary system forces premature rejection of prospects who have real pain but haven't yet built the measurement infrastructure to engage. In capital-intensive manufacturing, a VP Ops scoring 14 may be 90 days from a transformation project — they need to see the gap, not get a form rejection. DEFER keeps them in the pipeline with a specific follow-up action: "Here are the 2–3 questions where your score is low and what a PROCEED-level response would look like."

DEFER also protects the sales conversation: a prospect scoring 14 would likely fail the Discovery Call CoPQ calculation because they don't have enough data. Sending them to the call wastes both parties' time and generates an S2 defect.

**Rejected approach:** Binary PASS/FAIL. Discarded because it would reject 40–60% of engaged, pain-aware prospects who are not yet measurement-ready — the wrong reason to close a lead.

**Code location:** `recommend()` in `src/pillar3/scorecard.py`
**Test coverage:** `TestRecommendation::test_at_defer_lower_boundary_returns_defer`, `test_one_below_defer_lower_returns_reject`

---

## Decision 3 — Question banks are curated lists, not LLM-generated

**Date:** 2026-06-14
**Status:** Implemented (3 banks × 10 questions each)

**Decision:** Each scorecard type has a fixed ordered question bank in `QUESTION_BANKS`. Questions are selected by slicing the bank to `questions_count`. The LLM does not generate or modify questions at runtime.

**Reasoning:** If questions are generated dynamically, the scoring model becomes non-reproducible. Two prospects in the same industry, same role, same pain area could receive different questions and produce incomparable scores. The threshold (18/24) is only meaningful if the questions are consistent. Curated banks also allow calibration: if S2 defects cluster around specific questions, those questions can be reviewed and replaced by name.

Dynamic generation is useful for bespoke, one-off assessments. For a systematic qualification pipeline, consistency is more valuable than novelty.

**Rejected approach:** LLM generates 8 questions tailored to the specific prospect at runtime. Discarded because it makes threshold calibration impossible and scores incomparable across prospects.

**Code location:** `QUESTION_BANKS` constant, `generate_questions()` — `src/pillar3/scorecard.py`

---

## Decision 4 — S2 and S3 defect codes track false positives and false negatives

**Date:** 2026-06-14
**Status:** Defined in constants and system prompt; requires user to log post-event

**Decision:** S2 (passed scorecard, no commercial result) and S3 (failed scorecard, later converted via another channel) are first-class defect codes in the system, tracked in `outreach_log.md`.

**Reasoning:** The scorecard rubric is a hypothesis about what predicts commercial fit. Like any process hypothesis, it must be tested against outcomes. Without S2/S3 tracking, the threshold and question bank cannot be calibrated — they stay at their initial settings indefinitely regardless of whether they're working.

Three S2 defects indicate the threshold is too low (allowing through prospects who don't convert). Three S3 defects indicate the threshold is too high (blocking prospects who would have converted via another route). The three-strike rule prevents over-calibration from a single anomaly.

**Rejected approach:** Manual review without structured defect coding. Discarded because unstructured review relies on memory and recency bias — exactly what the system is designed to replace.

**Code location:** `DEFECT_CODES` constant — `src/pillar3/scorecard.py`; system prompt Step 4 and escalation section

---

## Decision 6 — Dual threshold system: cold vs warm lead qualification

**Date:** 2026-06-16
**Status:** Implemented and tested

**Decision:** The recommendation function applies different thresholds depending on whether the prospect has demonstrated inbound intent. Warm leads (any of: `inbound_dm`, `gated_content_download`, `requested_call`, `provided_copq_estimate`) are evaluated at PROCEED ≥14 / DEFER 8–13 / REJECT <8. Cold prospects retain the original PROCEED ≥18 / DEFER 12–17 / REJECT <12.

The signal is a named enum validated at runtime — invalid signals raise `ScorecardError`. The threshold applied is recorded in the markdown output and the outreach log entry.

**Reasoning:** Surfaced by CTest 1 simulation (Sarah Chen, Acme Aerospace). Score 12/24 correctly returned DEFER under cold thresholds, but Sarah was an inbound warm lead who had already identified £14M CoPQ and explicitly asked for a call. The operational gap exposed by Q7=0 (no formal CoPQ quantification) is not a barrier to a conversation — it is the reason for the conversation. Applying a uniform maturity threshold to inbound and outbound prospects creates false negatives on your highest-intent leads.

The 4-point reduction (18→14, 12→8) preserves the structure of the three-tier system. It does not override the scorecard with a qualitative judgment — it adjusts the scoring bar to reflect pre-demonstrated intent, which is a legitimate proxy for fit signal.

**Rejected approach:** Single threshold for all prospects. Discarded because it systematically filters out warm inbound leads who score low on Q7 (CoPQ not yet quantified) — the exact clients Olivia's engagement is designed to serve.

**Rejected approach:** Boolean `warm_lead` flag. Named signals (`inbound_dm`, `gated_content_download`, etc.) were chosen instead because they make the outreach log auditable — you can see not just that a prospect was warm, but why, which matters for S2 defect analysis.

**Code location:** `WARM_LEAD_SIGNALS`, `THRESHOLD_PASS_WARM`, `THRESHOLD_DEFER_LOW_WARM`, `recommend()`, `build_scorecard_markdown()`, `append_log_entry()` — `src/pillar3/scorecard.py`, `src/pillar3/outreach_log.py`
**Test coverage:** `TestWarmLeadRecommendation` — 14 tests covering both threshold boundaries, all three outcomes, signal validation, and explanation text

---

## Decision 7 — Integration stub: CoQPricer to Proposal Builder (2026-06-16)

**Date:** 2026-06-16
**Status:** Stub in place; awaiting Pillar 1 package installation

**Decision:** The integration layer (`src/pillar3/integration.py`) imports `src.pillar1.copq_pricing.calculate_fee`, which is currently a stub that raises `NotImplementedError`. This is intentional: it keeps the coupling explicit and testable (via mocking) without silently producing incorrect outputs in production.

**Plan:** Replace the stub with the actual Pillar 1 implementation once the Pillar 1 package is installed or symlinked into the project. Until then, the integration is only used in tests.

**Impact:** No blocking issue; the pipeline works in manual mode where fees are provided directly to the Proposal Builder.

**Code location:** `src/pillar3/integration.py`, `src/pillar1/copq_pricing.py` (stub)
**Test coverage:** `TestIntegration` — 2 tests; `calculate_fee` and `build_proposal` are mocked

---

## Decision 5 — Eval-first applied; 33 tests written before or alongside implementation

**Date:** 2026-06-14
**Status:** Enforced

**Decision:** Feature map written before source code. Level 1 tests written before or alongside implementation.

**Test coverage at build completion:**

| Class | Tests |
|-------|-------|
| TestGenerateQuestions | 6 |
| TestCalculateScore | 5 |
| TestMaxScore | 3 |
| TestRecommendation | 7 |
| TestValidateScorecard | 4 |
| TestScorecardMarkdown | 5 |
| TestOutreachLog | 3 |
| **Total** | **33** |

All 33 passing as of build completion (2026-06-14). Run with: `py -3.13 -m pytest evals/level1/ -v`
