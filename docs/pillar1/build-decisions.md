# Pillar 1 — Build Decisions Log
# System: Offer Design & Productization Agentic System
# Consultant: Olivia Key — The Systems Surgeon (oliviasmuse.com)
# Built: 2026-04-30 | Documented: 2026-06-14
# Test coverage at build completion: 22 tests, 3 agents, all passing

This document records every non-obvious architectural decision made during the build of the Pillar 1 Agentic System. It exists to:
1. Explain WHY the system works the way it does — not just what it does
2. Provide a citable record of methodology choices, gate design, and rejected alternatives
3. Enable future diagnostic work if behaviour drifts
4. Serve as a reproducible build reference for equivalent client systems

---

## Decision 1 — CTQ tree generation is gated behind SIPOC completion

**Date:** 2026-04-30
**Status:** Implemented and tested

**Decision:** The CTQ tree generator cannot be invoked without a completed, validated SIPOC (all 5 columns non-empty). This is a hard programmatic precondition — not a prompt instruction.

**Reasoning:** A CTQ tree translates enterprise needs into measurable quality requirements with LSL/USL bounds. If the SIPOC is incomplete — missing suppliers, inputs, outputs, or customers — the CTQ nodes will be scoped against a partial or incorrect delivery model. Downstream consequences: deliverables are built to the wrong quality targets, first-time acceptance rate falls, and the engagement opens with a structural defect.

The gate is enforced in code rather than in the system prompt because prompt-based instructions can be overridden by user pressure ("just give me the CTQ, I know my SIPOC"), model drift, or conversational context. Code cannot be argued with.

**Rejected approach:** Prompt instruction ("Only generate a CTQ if the user has provided a complete SIPOC"). Discarded because prompt-level gates are persuadable; code-level gates are not.

**Code location:** SIPOC completeness check before CTQ logic — `src/pillar1/sipoc.py`, `src/pillar1/ctq.py`
**Test coverage:** `TestSipocGate` — attempts CTQ without complete SIPOC; asserts gate blocks it

---

## Decision 2 — Subjective language blocklist, not LLM judgment

**Date:** 2026-04-30
**Status:** Implemented and tested (highest-risk failure mode: FM-02, RPN 192)

**Decision:** Quality criteria objectivity is enforced via a hard-coded blocklist (`good`, `clear`, `professional`, `appropriate`, `reasonable`, `high quality`, `sufficient`, `adequate`, `timely`, `well-structured`, etc.). LLM judgment is not used to assess objectivity.

**Reasoning:** A CTQ node or PPD quality criterion containing "professional" or "good" is uncheckable. If the first deliverable is disputed, the only defence is a measurable quality criterion — "deliverable accepted by client within 5 business days without revision" is defensible; "professional standard" is not. First-Time Acceptance Rate as a KPI only has meaning if acceptance is binary and criteria are unambiguous.

Using an LLM to judge whether language is subjective creates a recursive problem: the LLM's own language use tendencies make it a biased evaluator of its own output. A blocklist is deterministic, version-controlled, and auditable.

**Rejected approach:** LLM self-assessment of output objectivity ("Is this CTQ criterion measurable? Yes/No"). Discarded because LLM self-evaluation is unreliable on subjective-vs-objective boundaries — the same model that produces "appropriate" is unlikely to reliably flag it.

**Code location:** `check_quality_criteria_objectivity()` — `src/pillar1/ppd.py`
**Test coverage:** `TestQualityCriteriaObjectivity` — tests blocklist catches every blocked term; clean criteria pass

---

## Decision 3 — £5,000/month floor is a hard-coded constant, not an instruction

**Date:** 2026-04-30
**Status:** Implemented and tested

**Decision:** The pricing floor is defined as `PRICE_FLOOR_MONTHLY = 5000` in `copq.py`. Any CoPQ-derived pricing recommendation below this value is automatically replaced by the floor value. The system prompt does not instruct the agent to apply a floor — the code enforces it.

**Reasoning:** If the floor is in the system prompt, a low CoPQ input can produce a prompt-compliant response that violates the floor through framing ("at the 10% recovery rate, this engagement would be priced at £3,200/month, which is below your typical floor..."). The model is not always reliable on arithmetic and threshold enforcement when both are embedded in conversational instructions.

More importantly, the floor is not a preference — it is a positioning commitment. Violating it once, even in a "here's the number but remember your floor" output, hands the prospect an anchor that undermines every future negotiation.

**Rejected approach:** Prompt instruction ("Never recommend below £5,000/month"). Discarded because prompt-level pricing floors can be undermined by low-CoPQ inputs where the "right" calculation clearly suggests a lower number.

**Code location:** `PRICE_FLOOR_MONTHLY` constant — `src/pillar1/copq.py`
**Test coverage:** `TestCopqPricingFloor` — low CoPQ input; asserts output is always ≥£5,000/month

---

## Decision 4 — PPD quality check is in-pipeline, not post-review

**Date:** 2026-04-30
**Status:** Implemented and tested

**Decision:** The PPD quality check runs automatically as part of the PPD generation pipeline, before the output is returned to the user. It is not a separate step the user must request.

**Reasoning:** If the quality check is post-generation and user-triggered, there is a gap in which a defective PPD exists and may be acted on. In a consulting context, a PPD defines the acceptance criteria for a deliverable. A defective PPD that reaches a client (even as a draft) creates an implicit commitment that may be enforced. The check must run before the PPD leaves the system.

Trace logging records `quality_check_passed` for every PPD output. An absent field in the trace is itself a defect (FM-05), allowing quality check skipping to be detected retrospectively even if it somehow occurs.

**Rejected approach:** Optional user-triggered quality check ("Would you like me to check this PPD for quality?"). Discarded because optional checks are skipped under time pressure — exactly the conditions where defective PPDs are most likely to be generated and used.

**Code location:** Quality check pipeline step — `src/pillar1/ppd.py`; `quality_check_passed` field — `src/pillar1/trace.py`
**Test coverage:** `TestPPDPipeline` — asserts quality_check_passed is always present in trace output

---

## Decision 5 — ROI narrative requires a completed CoPQ object, not a number input

**Date:** 2026-04-30
**Status:** Implemented and tested

**Decision:** The ROI narrative generator accepts a CoPQ calculation object (not a raw number) as its required input. If no completed CoPQ object is provided, a `ROIAnchorError` is raised before any narrative is generated.

**Reasoning:** An ROI narrative built on an unanchored figure ("I estimate recovery of around £500k...") is worse than no narrative at all — it gives the prospect a number they can challenge without the itemised calculation that defends it. The entire value of the CoPQ methodology in a proposal is that the prospect self-discovers the cost in a structured four-category breakdown. The narrative must reference that specific breakdown, not a standalone estimate.

Requiring the full CoPQ object (not just a total) also prevents a common failure mode: user provides £500k as a headline figure, ROI narrative is generated, but the breakdown that justifies the figure was never done. The proposal then contains an undefendable claim.

**Rejected approach:** Accept a raw numeric CoPQ value. Discarded because it removes the audit trail between the breakdown and the narrative, and enables ROI claims without the evidential foundation.

**Code location:** `ROIAnchorError` guard — `src/pillar1/copq.py`
**Test coverage:** `TestROIAnchor` — calls ROI narrative without CoPQ object; asserts ROIAnchorError raised

---

## Decision 6 — Eval-first applied across all 3 agents

**Date:** 2026-04-30
**Status:** Enforced across entire build

**Decision:** Feature map written before source code. Level 1 tests written before or alongside implementation. No agent feature exists without a corresponding falsifiable assertion in `evals/level1/`.

**Reasoning:** Applied Hamel Husain's eval framework at Level 1 minimum. The test suite ships as part of the deliverable. The known failure modes document (FMEA with RPN scores) was written before the build — every FM has a corresponding Level 1 test designed to detect it. This inverts the standard development pattern: failure modes first, tests second, code third.

The highest-risk failure mode (FM-02: subjective language, RPN 192) has corresponding tests that would catch a regression if the blocklist were accidentally shortened or bypassed. Without eval-first discipline, a future change to `ppd.py` could re-introduce subjective language without detection.

**Test coverage at build completion:**

| Module | Test file | Tests |
|--------|-----------|-------|
| SIPOC + CTQ gate | test_sipoc.py | 8 |
| PPD generation + quality check | test_ppd.py | 7 |
| CoPQ calculation + pricing + ROI | test_copq.py | 7 |
| **Total** | | **22** |

All 22 tests passing as of build completion. Run with: `py -3.13 -m pytest evals/level1/ -v`
