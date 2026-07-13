# Changelog — Olivia Key Agentic Operating System
# Pillars 0-7 (Pillar 8 — orchestration — planned, not yet built)

All notable changes to this monorepo are documented here. Format per entry:
date · version · what changed · why · files affected · review question.

Change types: NEW | FIX | CHORE | DOCS | REFACTOR | THRESHOLD

---

## [1.0.0] — 2026-07-13

### NEW — Monorepo consolidation

Pillars 0-7 unified into a single monorepo at `C:\Users\olivi\dev\olivia-key-agentic-os\`.

**Before:** 8 separate directories, each with its own copy of `.gitignore`, `LICENSE`, `README.md`, `CLAUDE.md`, `CHANGELOG.md`, `requirements.txt`. Cross-pillar imports bypassed the public interface. RPN thresholds duplicated across Pillar 3 and Pillar 4. Defect codes drifted between pillars (e.g., `S1` had three different meanings).

**After:** One monorepo with shared `src/common/`, consistent cross-pillar imports, single source of truth for defect codes and FMEA thresholds.

**Files affected:** All pillar source moved from `C:\Users\olivi\dev\olivia-key-pillar-N\` to `src/pillarN/` in the monorepo. Originals kept as backup per user instruction.

**Review question (2026-10-13):** Is the `src/common/` module being used consistently across all pillars? Are defect codes still drifting?

---

### NEW — `src/common/` shared module

Four new files in `src/common/`:

- `trace.py` — consolidated trace logger (replaces 7 near-identical copies across pillars 1-7)
- `defect_codes.py` — central registry of all 70+ defect codes with `get_defect()`, `list_defects()`, `all_defect_codes()` helpers
- `fmea.py` — shared `calculate_rpn()`, `classify_rpn()`, `RPN_ACTION_THRESHOLD = 150`, `RPN_ANDON_THRESHOLD = 300` (single source of truth)
- `andon.py` — `is_andon_signal()`, `format_andon()`, `format_defect()` helpers; central ANDON_PHRASES tuple

**Why:** The 7 near-identical `trace.py` files were the worst duplication. Defect code drift was a real risk (e.g., `S1` had three different meanings across Pillar 0 scorecard, Pillar 3 scorecard, Pillar 3 gatekeeper). RPN thresholds were duplicated as module-level constants in Pillar 3 and Pillar 4.

**Review question:** Are the cross-pillar migrations done? Have any pillar's `DEFECT_CODES` been left drifting from the central registry?

---

### FIX — Test basename collisions

Multiple pillars had identically-named test files (`test_p0_cross_pillar.py`, `test_pillar0_integration.py`) which caused pytest collection errors when run together.

**Files affected:** Renamed in pillars 2, 3, 5, 6 to `test_pN_p0_cross_pillar.py` and `test_pN_pillar0_integration.py`.

---

### FIX — Stale test data in Pillar 6 invoicing tests

Five Pillar 6 tests used hardcoded invoice dates (e.g., `'2026-06-25'`) that have aged past the Net 14 payment window, causing them to fail when run on 2026-07-13.

**Files affected:** `evals/level1/pillar6/test_invoicing.py`, `evals/level1/pillar6/test_p6_p0_cross_pillar.py`. Replaced hardcoded dates with `_days_ago(5)` helper.

---

### FIX — Invalid Anthropic model name in Pillar 1

`src/pillar1/agent_runner.py` had `MODEL = "claude-opus-4-8"` — not a valid Anthropic model name. Replaced with `MODEL = os.environ.get("PILLAR1_MODEL", "claude-opus-4-5")` — configurable via env var with a sensible default.

---

### FIX — Word-boundary regex in Pillar 0 positioning

The `_count_specificity_markers()` and `has_subjective_language()` functions in `src/pillar0/positioning.py` used substring matching, causing false positives like "md" matching in "demand". Now uses precompiled word-boundary regex with smart fallback for symbol keywords (`£`, `%`).

---

### DOCS — Major doc drift fix in Pillars 4-7

CLAUDE.md in Pillars 4, 5, 6, 7 each claimed only one agent was built. Reality: 4-6 agents were actually built and tested. Rewrote each CLAUDE.md to reflect the actual agent count, expanded the project structure listings, and added full defect code tables.

---

### DOCS — Test count updates in CLAUDE.md files

Pillar 2 CLAUDE.md: 138 → 167
Pillar 3 CLAUDE.md: 84 → 149
Pillar 4 CLAUDE.md: 40 → 163
Pillar 5 CLAUDE.md: not documented → 193
Pillar 6 CLAUDE.md: not documented → 155
Pillar 7 CLAUDE.md: not documented → 109

---

### CHORE — Olivia hard-codes generalised to "Owner"

Pillar 0 source had hardcoded `"Olivia"` as default for `discount_authority`, `global_discount_authority`, and `escalation_path`. Replaced with `"Owner"` to make the system generalisable beyond one operator. Tests updated accordingly.

---

### CHORE — Renamed DistributionAuthority methods

`DistributionAuthority.is_primary(name)` and `is_secondary(name)` renamed to `is_primary_channel(name)` and `is_secondary_channel(name)` to disambiguate from the `Channel.is_primary` boolean field.

---

## Pre-monorepo history

Per-pillar CHANGELOGs are preserved at `docs/pillarN/CHANGELOG.md` (in some pillars) or in the original `C:\Users\olivi\dev\olivia-key-pillar-N\CHANGELOG.md` files. The original pillar directories are kept as backup per user instruction; they can be deleted after the monorepo is verified in production.

---

Next entry: append below with date, version, change type, and review question.
