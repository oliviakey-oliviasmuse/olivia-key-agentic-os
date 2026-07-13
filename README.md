<div align="center">

# Olivia Key — Agentic Operating System

**Pillars 0–7 of a Lean Six Sigma / PRINCE2 / CoPQ agentic OS for solo B2B consulting.**
**Deterministic gates. Eval-first. Zero subjective language.**

[![Tests](https://img.shields.io/badge/tests-1315%20passing-4CAF50?logo=pytest&logoColor=white)](evals/level1/)
[![CI](https://github.com/oliviakey-oliviasmuse/olivia-key-agentic-os/actions/workflows/tests.yml/badge.svg)](https://github.com/oliviakey-oliviasmuse/olivia-key-agentic-os/actions/workflows/tests.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Methodology](https://img.shields.io/badge/methodology-LSS%20%7C%20PRINCE2%20%7C%20CoPQ-0055A4)](docs/)
[![License: MIT](https://img.shields.io/badge/license-MIT-22c55e)](LICENSE)

[Overview](#overview) · [Pillars](#the-8-pillars) · [Architecture](#architecture) · [Quick Start](#quick-start) · [Test Suite](#test-suite) · [Contributing](#contributing)

</div>

---

## Overview

A deterministic, gate-enforced agentic system for solo B2B consulting practices. Eight pillars, each enforcing a specific LSS/strategy discipline as Python code with hard-typed gates, defect codes, and YAML persistence.

Every constraint that matters — the SIPOC gate before CTQ, the £5,000/month price floor, the subjective language blocklist — is enforced programmatically. A language model can be argued out of an instruction. It cannot be argued out of a `ValueError`.

This is the monorepo — all 8 pillars in one place, sharing common utilities. Pillar 8 (orchestration) is planned for a later date.

## The 8 Pillars

| # | Pillar | What it does | Agents | Tests |
|---|--------|--------------|--------|-------|
| 0 | **Strategy & Positioning** | ICP, voice rules, offer menu, drift detection, distribution authority, strategic memory — the foundation every other pillar reads from | 8 | 357 |
| 1 | **Offer Design & Productization** | SIPOC mapper, CTQ tree (gated by SIPOC), PRINCE2 PPD (with quality self-check), CoPQ pricing engine | 4 | 22 |
| 2 | **Marketing & Demand Generation** | 8-gate content quality audit, market signal monitor, hypothesis generator, monthly strategy optimizer | 4 | 167 |
| 3 | **Sales & Client Acquisition** | Scorecard (warm/cold thresholds), ICP gatekeeper, discovery call analyser, FMEA-backed proposal builder | 4 | 149 |
| 4 | **Client Delivery & Success** | PID/RACI generator, Control Plan (CTQ + FMEA), FTAR tracker, NPS tracker, Case Study Writer | 5 | 163 |
| 5 | **Operations & Governance** | 5Ms allocation, Issue Register, cycle time, defect monitor, SOP writer, drift monitor wrapper | 6 | 193 |
| 6 | **Finance & Commercial** | Invoicing (Net 14), budget variance, net worth tracker, unit economics dashboard | 4 | 155 |
| 7 | **Knowledge, Systems & Improvement** | Lessons Report (PRINCE2), framework library manager, product pipeline tracker | 3 | 109 |

**Total: 36 agents, 1,315 tests, 1 monorepo.**

## Design Philosophy

This system was built on one principle: **gates belong in code, not in instructions.**

| Constraint | Enforcement |
|------------|-------------|
| No CTQ without complete SIPOC | `SIPOCValidationError` raised before CTQ logic executes |
| No subjective language in CTQ/PPD/output | Word-boundary regex against a multi-pillar blocklist |
| Price never below £5,000/month | `PRICE_FLOOR_MONTHLY` constant — code, not prompt |
| PPD quality check cannot be skipped | In-pipeline, not user-triggered; trace log field is non-optional |
| ROI narrative requires numeric CoPQ anchor | `ROIAnchorError` if no completed CoPQ object passed |
| FMEA RPN >=300 must be reviewed before handover | `RPN_ANDON_THRESHOLD = 300` constant in `src/common/fmea.py` |
| FMEA RPN >=150 requires explicit control plan | `RPN_ACTION_THRESHOLD = 150` constant in `src/common/fmea.py` |
| No CTQ without explicit mapping in strict mode | Hard `ValueError` in `control_plan.py` |
| Voice rules violations (P0 A3) gate P2 content | Cross-pillar gate G18, fail-open with warning |
| Channel authority (P0 A6) gates P2 publishing | Cross-pillar gate G19, fail-open with warning |
| ICP membership (P0 A3) hard-rejects in P3 scorecard | P0 ICP gate, fail-closed (hard REJECT) |
| Price floor (P0 A4) gates P3 proposals and P6 invoices | P0 price floor gate, M1/M2 defects |

Applied Hamel Husain's eval framework at Level 1 minimum: failure modes written first (FMEA with RPN scores), then tests, then code. Every feature ships with a falsifiable assertion.

## Architecture

```
olivia-key-agentic-os/
├── README.md                          ← you are here
├── CHANGELOG.md                       ← cross-pillar changes
├── CLAUDE.md                          ← contributor guide (Claude Code context)
├── LICENSE                            ← MIT
├── .gitignore
├── conftest.py                        ← pytest path setup
├── pyproject.toml                     ← workspace config
├── requirements.txt
├── docs/
│   ├── architecture.md                ← how the pillars fit together
│   ├── cross-pillar-defect-codes.md   ← single source of truth
│   ├── cross-pillar-gates.md          ← P0 → P2/P3/P6 gate wiring
│   ├── fail-open-policy.md            ← why missing config = pass=True
│   ├── fmea-rpn-thresholds.md         ← single source for RPN_ACTION=150, RPN_ANDON=300
│   └── pillarN/                       ← per-pillar docs (agent-overview, build-decisions, FMEA)
├── src/
│   ├── common/                        ← shared utilities
│   │   ├── trace.py                   ← ONE trace logger (replaces 7 duplicates)
│   │   ├── defect_codes.py            ← central registry of all 70+ defect codes
│   │   ├── fmea.py                    ← shared RPN helpers
│   │   └── andon.py                   ← ANDON phrase recognition + formatting
│   ├── pillar0/                       ← foundation
│   ├── pillar1/                       ← offer design
│   ├── pillar2/                       ← marketing
│   ├── pillar3/                       ← sales
│   ├── pillar4/                       ← delivery
│   ├── pillar5/                       ← operations
│   ├── pillar6/                       ← finance
│   └── pillar7/                       ← learning
├── evals/
│   ├── level1/                        ← per-pillar unit tests
│   │   ├── pillar0/  (8 files, 357 tests)
│   │   ├── pillar1/  (3 files, 22 tests)
│   │   ├── pillar2/  (6 files, 167 tests)
│   │   ├── pillar3/  (9 files, 149 tests)
│   │   ├── pillar4/  (9 files, 163 tests)
│   │   ├── pillar5/  (7 files, 193 tests)
│   │   ├── pillar6/  (6 files, 155 tests)
│   │   └── pillar7/  (3 files, 109 tests)
│   ├── traces/                        ← runtime trace data
│   └── fixtures/                      ← shared test fixtures
└── scripts/
```

## Cross-pillar wiring

Pillar 0 is the foundation. Every other pillar reads from it through cross-pillar gates. The pattern is consistent:

- **Pillar 2 (Marketing)** uses Pillar 0's `is_in_icp` (via `p0_interface`) and `check_channel_allowed` (via `p0_interface`) for gates G18 and G19
- **Pillar 3 (Sales)** uses Pillar 0's `validate_prospect`, `check_icp_membership`, and `check_price_floor` for hard-reject and price-floor gates
- **Pillar 5 (Operations)** uses Pillar 0's `run_weekly_drift_review` for strategic drift monitoring
- **Pillar 6 (Finance)** uses Pillar 0's `check_price_floor` for invoice below-floor detection

All cross-pillar gates are **fail-open** when Pillar 0 is unavailable (returns `pass=True` with `source: "fail-open"` marker). The fail-open is documented and auditable.

## Quick Start

### Prerequisites

- Python 3.10+ (developed against 3.13)
- Git

### Clone and install

```bash
git clone https://github.com/oliviakey-oliviasmuse/olivia-key-agentic-os.git
cd olivia-key-agentic-os
pip install -r requirements.txt
```

### Run the test suite

```bash
py -3.13 -m pytest evals/level1/ -v
```

Expected output: **1315 passed in ~1.3s**.

No LLM or API key required for the deterministic test layer.

### Use a specific pillar

```python
# Cross-pillar style (recommended for new code)
from src.pillar0.icp_positioning import is_in_icp, Positioning
from src.pillar3.gatekeeper import score_prospect
from src.common.defect_codes import get_defect
from src.common.fmea import calculate_rpn, classify_rpn

# Pillar-prefixed style (Pillar 1's existing convention)
from pillar1.copq import calculate_copq, generate_roi_narrative
```

## Test Suite

1,315 tests across 51 test files. All run without an LLM or API key.

| Pillar | Test files | Tests |
|--------|-----------|-------|
| 0 — Strategy & Positioning | 8 | 357 |
| 1 — Offer Design & Productization | 3 | 22 |
| 2 — Marketing & Demand Generation | 6 | 167 |
| 3 — Sales & Client Acquisition | 9 | 149 |
| 4 — Client Delivery | 9 | 163 |
| 5 — Operations & Governance | 7 | 193 |
| 6 — Finance & Commercial | 6 | 155 |
| 7 — Knowledge & Improvement | 3 | 109 |
| **Total** | **51** | **1,315** |

**Failure mode coverage:** Every failure mode documented in each pillar's `docs/known-failure-modes.md` has a corresponding Level 1 test.

## Contributing

This repository represents a live consulting system. Contributions that improve test coverage, add documented failure modes, or strengthen gate logic are welcome.

**Before raising a pull request:**
1. Read [`CLAUDE.md`](CLAUDE.md) for project conventions
2. Ensure all 1,315 tests pass: `py -3.13 -m pytest evals/level1/ -v`
3. Any new feature must include a corresponding entry in the relevant `evals/feature-map.md` and a Level 1 test
4. New defect codes must be added to `src/common/defect_codes.py` (one source of truth)
5. No PR merges without green CI

## License

MIT — see [`LICENSE`](LICENSE). Free to use, adapt, and distribute, including for commercial consulting work. Attribution appreciated but not required.

## Origin and context

This system was designed by [Olivia Key](https://oliviasmuse.com) as the operating system for her independent consulting practice. The methodology combines Lean Six Sigma, PRINCE2, and Cost of Poor Quality analysis — applied to B2B consulting operations rather than manufacturing.

Each pillar was developed in collaboration with Claude (Anthropic) as a structured pair-programming partner. All design decisions, defect codes, and gate logic are documented in the per-pillar `CHANGELOG.md` with the rationale captured at the time of decision.
