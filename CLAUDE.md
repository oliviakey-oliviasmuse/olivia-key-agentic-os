# Olivia Key — Agentic Operating System (Monorepo)
# Pillars 0–7 of the Master Operating Blueprint

## What This Project Does

A deterministic, gate-enforced agentic system for a solo B2B consulting practice. Eight pillars, each enforcing a specific LSS / PRINCE2 / CoPQ discipline as Python code with hard-typed gates, defect codes, and YAML persistence.

| Pillar | Module | What it does |
|--------|--------|--------------|
| 0 | `src/pillar0/` | Strategy & Positioning: ICP, voice rules, offer menu, drift detection, distribution authority, strategic memory — the foundation every other pillar reads from |
| 1 | `src/pillar1/` | Offer Design & Productization: SIPOC mapper, CTQ tree, PRINCE2 PPD, CoPQ pricing engine |
| 2 | `src/pillar2/` | Marketing & Demand Generation: 8-gate content quality audit, market monitor, hypothesis generator, strategy optimizer |
| 3 | `src/pillar3/` | Sales & Client Acquisition: Scorecard, ICP gatekeeper, discovery analyser, FMEA-backed proposal builder |
| 4 | `src/pillar4/` | Client Delivery: PID/RACI, Control Plan, FTAR tracker, NPS tracker, case study writer |
| 5 | `src/pillar5/` | Operations & Governance: 5Ms, Issue Register, cycle time, defect monitor, SOP writer, drift monitor |
| 6 | `src/pillar6/` | Finance & Commercial: Invoicing (Net 14), budget variance, net worth, unit economics |
| 7 | `src/pillar7/` | Knowledge & Improvement: Lessons Report, framework library, product pipeline |

## Non-Negotiable Rules (apply across all pillars)

### Stage gates (enforced in code, never in instructions)

Every critical decision has a hard `ValueError` or explicit check in code, not in a prompt. The LLM can be argued out of an instruction; it cannot be argued out of a `ValueError`.

### Cross-pillar import rules

1. **Pillar 0 is the foundation.** Every other pillar may import from `src.pillar0.public` (re-exports of cross-pillar gate functions).
2. **Use `src.common` for shared utilities** — trace, defect codes, FMEA, ANDON phrases.
3. **Never import directly from another pillar's internal modules** — use the public surface.
4. **Cross-pillar gates are fail-open** when Pillar 0 is unavailable (returns `pass=True` with `source: "fail-open"` marker). This is documented and auditable.

### Two-layer architecture

Each agent follows the deterministic + generator split:
- **Deterministic layer** (`<agent>.py`) — dataclasses, gates, pure functions, fully testable
- **Generator layer** (`<agent>_generator.py`) — LLM-facing wrapper with dict-based API

The deterministic layer can be tested, versioned, and audited independently of any model.

### Defect codes

All defect codes are registered in `src/common/defect_codes.py` (single source of truth). 70+ unique codes across the 8 pillars. Use `get_defect(code, pillar)` for pillar-specific lookups; `list_defects(pillar)` for all codes in a pillar.

### Trace logging (mandatory)

Every agent interaction logs to `evals/traces/` via `src.common.trace.log_trace()`. Required fields: timestamp, agent, version, feature, inputs_hash, confidence, defects_logged, output_artifact, quality_check_passed, gate_triggered, gate_reason, human_override, lessons_report_trigger, andon_triggered.

### FMEA RPN thresholds (single source of truth)

```python
from src.common.fmea import RPN_ACTION_THRESHOLD, RPN_ANDON_THRESHOLD
# RPN_ACTION_THRESHOLD = 150  (requires explicit control plan)
# RPN_ANDON_THRESHOLD = 300   (must be reviewed before handover)
```

These are used by Pillar 3 (proposal_builder) and Pillar 4 (control_plan). Do not duplicate as module-level constants — import from `src.common.fmea`.

### ANDON phrase recognition

```python
from src.common.andon import is_andon_signal, format_andon
if is_andon_signal(llm_response):
    log_trace(... andon_triggered=True ...)
```

Phrases: `"ANDON STOP"`, `"ANDON –"`, `"DEFECT –"`. Centralised in `src/common/andon.py`.

## Python Version

Use `py -3.13` for all commands. The default Python install may be 3.14 and is missing packages.

## Running Tests

```bash
# All tests across all 8 pillars
py -3.13 -m pytest evals/level1/ -v

# Just one pillar
py -3.13 -m pytest evals/level1/pillar3/ -v

# Just one test file
py -3.13 -m pytest evals/level1/pillar0/test_positioning.py -v
```

Expected: **1315 passed in ~1.3s** for the full suite.

## Project Structure

```
olivia-key-agentic-os/
├── README.md
├── CHANGELOG.md
├── CLAUDE.md                          ← you are here
├── LICENSE                            ← MIT
├── .gitignore
├── conftest.py                        ← pytest path setup (adds monorepo root + src to sys.path)
├── pyproject.toml                     ← workspace config
├── requirements.txt
├── docs/
│   ├── architecture.md
│   ├── cross-pillar-defect-codes.md
│   ├── cross-pillar-gates.md
│   ├── fail-open-policy.md
│   ├── fmea-rpn-thresholds.md
│   └── pillarN/                       ← per-pillar docs (8 dirs)
├── src/
│   ├── common/                        ← shared utilities
│   ├── pillar0/                       ← foundation
│   ├── pillar1/
│   ├── pillar2/
│   ├── pillar3/
│   ├── pillar4/
│   ├── pillar5/
│   ├── pillar6/
│   └── pillar7/
├── evals/
│   ├── level1/
│   │   ├── pillar0/
│   │   ├── pillar1/
│   │   ├── pillar2/
│   │   ├── pillar3/
│   │   ├── pillar4/
│   │   ├── pillar5/
│   │   ├── pillar6/
│   │   └── pillar7/
│   ├── traces/                        ← runtime trace data
│   └── fixtures/                      ← shared test fixtures
└── scripts/
```

## KPIs This System Supports

See each pillar's `CLAUDE.md` (archived at `docs/pillarN/`) for pillar-specific KPIs. Top-level metrics tracked by `src/common/trace.py:get_trace_summary()`:

- **Total traces** (interactions logged)
- **Defect rate** (% of traces with defects)
- **Gate trigger rate** (% of traces with gate_triggered=True)
- **ANDON rate** (% of traces with andon_triggered=True)
- **Average confidence** (mean LLM confidence across traces)
- **Human override rate** (% of traces with human_override=True)

## Failure Modes (cross-pillar)

- **Cross-pillar import violation** — direct import from another pillar's internal module. Use the public surface.
- **Defect code drift** — same code, different meanings across pillars. Always register in `src/common/defect_codes.py` first.
- **RPN threshold drift** — duplicating RPN constants instead of importing from `src.common.fmea`.
- **Fail-open without warning** — when Pillar 0 is unavailable, the gate must return `source: "fail-open"` (not just silent `pass=True`).
- **Test basename collision** — multiple pillars with `test_p0_cross_pillar.py` conflict in pytest. Use `test_pN_p0_cross_pillar.py` naming.
- **Stale test data** — hardcoded dates in test fixtures age out of validity windows (e.g., invoice dates that fall past Net 14). Use relative dates (`_days_ago(N)` or `datetime.now() - timedelta(days=N)`).
