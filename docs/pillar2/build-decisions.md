# Pillar 2 — Build Decisions Log
# System: Marketing & Demand Generation Agentic System
# Consultant: Olivia Key — The Systems Surgeon (oliviasmuse.com)
# Built: 2026-06-14
# Test coverage at build completion: 138 tests, 4 agents, all passing

This document records every non-obvious architectural decision made during the build of the Pillar 2 Agentic System. It exists to:
1. Explain WHY the system works the way it does — not just what it does
2. Provide a citable record of methodology choices, calibration reasoning, and rejected alternatives
3. Enable future diagnostic work if behaviour drifts or results diverge from design intent
4. Serve as a reproducible build reference for equivalent client systems

---

## Decision 1 — ANDON fires on gate identity, not pass rate

**Date:** 2026-06-14
**Status:** Implemented and tested

**Decision:** ANDON STOP fires only when G12, G13, or G14 specifically fail. It does not fire when overall pass rate drops below any threshold.

**Context:** Initial implementation used `ANDON_THRESHOLD = 0.70`. A post failing 3 out of 8 gates (62.5% pass rate) would trigger ANDON STOP regardless of which gates failed.

**Reasoning:** G12 (hype words), G13 (citation integrity), and G14 (E-E-A-T) carry qualitative reputational risk that no amount of corrective action can safely override before publication. A post can fail G5 (word count), G10 (vanity metrics), and G16 (CTA) simultaneously and be revised and published. A post with a single fabricated McKinsey citation cannot be revised and published quickly — the risk is reputational and legal. Conflating these categories with a threshold creates false safety: a post failing G12 at 72% overall pass rate would slip through the threshold gate.

**Rejected approach:** Pass-rate threshold (ANDON_THRESHOLD = 0.70). Discarded because it fires on volume of failures, not nature of failures — a fundamentally different quality signal.

**Code location:** `aggregate_verdict()` — `src/pillar2/content_gate.py`
**Test coverage:** `TestAggregateVerdict::test_many_non_andon_failures_returns_fail_not_andon`

---

## Decision 2 — G13 calibrated as two-path: case study vs general post

**Date:** 2026-06-14
**Status:** Implemented and tested

**Decision:** G13 evaluates content via two distinct paths:
- **Case study posts** (first-party language + verifiable £/% outcomes): pass with 1 source
- **General informative posts**: require ≥3 external source indicators or verified named sources

**Context:** Tested against three drafts of a LinkedIn post. Draft v3 — first-person narration, real client results, no external citations — triggered ANDON under the original single-path rule. Draft v2 — with MIT Study 2023, Gartner 2025 Survey, Dr. Jane Smith — passed despite all three citations being fabricated. The calibration reversed this outcome correctly.

**Reasoning:** Credibility is source-type dependent in B2B practitioner content. For a consultant whose expertise is the product, first-party case study evidence ("I helped a Tier-1 supplier recover £340,000 in six months") carries higher epistemic weight for a prospective client than an aggregated industry statistic from a third party. The reader's purchase decision depends on proof you've done it — not proof that someone else wrote about it. Requiring ≥3 external sources on a case-study post penalises exactly the content most likely to convert.

**Rejected approach:** Single-path keyword count (study, research, expert, data from, http). Discarded because it cannot distinguish between first-party evidence and generic citation references, producing systematically wrong verdicts on case-study content.

**Code location:** `_is_case_study_format()`, `check_g13_sources()` — `src/pillar2/content_gate.py`
**Test coverage:** `TestG13Sources` — 15 tests covering both paths, edge cases, and ANDON aggregation

---

## Decision 3 — Named source verification before G13 can pass

**Date:** 2026-06-14
**Status:** Implemented and tested

**Decision:** Any named external source detected in the text — known institutions (MIT, Gartner, McKinsey, etc.) near document keywords, Dr./Prof names, or year-prefixed titled documents — must be confirmed in a `verified_sources` parameter before G13 passes. Unverified named sources fire ANDON immediately.

**Context:** Draft v2 LinkedIn post, written with AI assistance, contained "MIT Study 2023", "2025 Gartner Cost of Quality Survey", and "Dr. Jane Smith". None could be verified. The original G13 implementation counted these as positive source signals and would have passed the post through. Named source detection was added specifically in response to this observed failure mode.

**Reasoning:** For a named practitioner selling advisory services, a fabricated citation constitutes misrepresentation and is a category error — not a formatting defect. The damage is asymmetric: a false negative (hallucinated citation published) causes lasting reputational harm; a false positive (real citation temporarily blocked for verification) causes a brief delay. The gate must enforce verification at the source, before publication, not flag citations post-publication.

Detection uses sentence-level institution scanning (known institution appearing in same sentence as a document-type keyword) plus regex patterns for Dr./Prof names and year-titled documents. Named sources are deduplicated.

**Rejected approach:** Soft non-blocking warning. Discarded on grounds of risk asymmetry — the cost of a missed hallucinated citation exceeds the cost of a verification step by several orders of magnitude for a credibility-dependent business.

**Code location:** `extract_named_sources()`, `check_g13_sources(verified_sources=)` — `src/pillar2/content_gate.py`
**Test coverage:** `TestExtractNamedSources` (6 tests), `TestG13Sources::test_named_institution_without_verified_sources_fails`, `test_partially_verified_named_sources_fails`

---

## Decision 4 — G17 funnel alignment enforced as two hard rules

**Date:** 2026-06-14
**Status:** Implemented and tested (defect code M11)

**Decision:** Two hard programmatic rules:
1. Hygiene (TOFU) content cannot carry a BOFU commercial objective (enquiries, client_calls)
2. Hero (BOFU) content must contain first-party case study data

**Reasoning for Rule 1:** TOFU content builds awareness in a cold audience with no relationship context. Placing a "DM me to book a call" CTA on a 200-word educational post creates cognitive dissonance — the reader has not accumulated sufficient trust to act on a high-commitment ask. Publishing TOFU content with a BOFU objective wastes CTA impressions, trains the algorithm on low-engagement closing attempts, and erodes the brand voice built across Hygiene content.

**Reasoning for Rule 2:** At BOFU, the prospect is evaluating a specific person as a potential hire. Generic industry statistics answer "is this problem real?" — they do not answer "can this specific person solve it for me?" First-party client outcomes (£340k recovered, 40% defect reduction in 6 months) are the only evidence type that answers the actual BOFU question. Generic external data at BOFU is a conversion leak: it confirms the problem without confirming the solution provider.

**Not blocked:** Hub (MOFU) with a BOFU objective. A detailed 400–600 word piece can carry an enquiry CTA because the reader has invested sufficient attention to be in the consideration phase. This is MOFU-to-BOFU nurturing, a valid funnel transition.

**Rejected approach:** Warning (non-blocking). Discarded because funnel misalignment is a systematic waste — content produced with the wrong objective consumes the same production effort as correctly aligned content and produces a fraction of the commercial result.

**Code location:** `check_g17_funnel_alignment()` — `src/pillar2/content_gate.py`
**Test coverage:** `TestG17FunnelAlignment` — 10 tests including both hard rules and the MOFU-to-BOFU allowed case

---

## Decision 5 — Agent 4 (Strategy Optimizer) kept separate from Agent 2 (Market Monitor)

**Date:** 2026-06-14
**Status:** Implemented and tested

**Decision:** Strategy Optimizer (Agent 4) is a standalone fourth agent, not merged with Market Monitor (Agent 2).

**Context:** An external AI tool proposed a merged "Market Intelligence" agent combining external trend scanning (Agent 2's function) and internal performance analysis (Agent 4's function) into a single agent.

**Reasoning:** The two agents operate on fundamentally different data sources, cadences, and decisions:

| Dimension | Agent 2 — Market Monitor | Agent 4 — Strategy Optimizer |
|-----------|--------------------------|------------------------------|
| Data source | External: trends, VOC, competitors, AI visibility | Internal: GA4, CRM, LinkedIn analytics, email |
| Cadence | Weekly | Monthly |
| Output feeds | Agent 3 (what to create) | Budget allocation and channel tactic decisions |
| Core question | "What is the market paying attention to?" | "Is what we're producing actually working commercially?" |
| Defect codes | None (output feeds Agent 3) | D1–D4 (recommendation accuracy) |

Merging these produces an agent with incoherent inputs, mismatched cadence, and entangled logic. The tests for a merged agent cannot isolate whether a trend-scoring failure or an ROI calculation failure produced a wrong recommendation. Separate agents → separate test classes → falsifiable assertions → diagnosable failures.

**Rejected approach:** Merged Market Intelligence agent. Evaluated and rejected on grounds of functional incoherence and test isolation.

**Code location:** `src/pillar2/strategy_optimizer.py`, `src/system_prompts/agent_strategy_optimizer.md`
**Test coverage:** `test_strategy_optimizer.py` — 40 tests

---

## Decision 6 — Eval-first applied across all 4 agents

**Date:** 2026-06-14
**Status:** Enforced across entire build

**Decision:** Feature map written before source code. Level 1 tests written before or alongside implementation. No agent feature exists without a corresponding falsifiable assertion in `evals/level1/`.

**Reasoning:** Applied Hamel Husain's eval framework at Level 1 minimum. The test suite ships as part of the deliverable — not as a post-build quality check. Without eval-first discipline:
- The system becomes a black box that "looks like it works" until a specific input triggers an untested case
- Calibration decisions (G13 two-path, named source verification, G17 hard rules) cannot be defended without test evidence
- Any future modification breaks silently rather than loudly
- The gate logic cannot be demonstrated as correct to a client or auditor without a runnable assertion

The ANDON threshold error (Decision 1) was caught because the test `test_many_non_andon_failures_returns_fail_not_andon` existed and failed against the initial implementation. Without this test, an incorrect ANDON trigger could have propagated undetected.

**Test coverage at build completion:**

| Agent | Test file | Tests |
|-------|-----------|-------|
| Agent 1 — Content Quality Gate | test_content_gate.py | 65 |
| Agent 2 — Market Monitor | test_market_monitor.py | 20 |
| Agent 3 — Content Hypothesis Generator | test_hypothesis_gen.py | 13 |
| Agent 4 — Strategy Optimizer | test_strategy_optimizer.py | 40 |
| **Total** | | **138** |

All 138 tests passing as of build completion (2026-06-14). Run with: `py -3.13 -m pytest evals/level1/ -v`
