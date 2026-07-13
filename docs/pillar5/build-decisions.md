# Build Decisions — Pillar 5: Operations & Governance

## Decision 1 — Per-field ValueError messages (not a single combined check)
**Chosen:** Each gate (G1–G5) raises a distinct ValueError naming the missing field.
**Rejected:** Single catch-all check listing all missing fields at once.
**Why:** Tests assert field name in exception message; specific errors are easier to surface in logs and ANDON output.

## Decision 2 — ANDON fires at trigger_count ≥ 3, SOP still generated
**Chosen:** Warn but continue — prepend ANDON block to markdown output.
**Rejected:** Hard block — raise exception, refuse to generate.
**Why:** The rule is "write SOP before 3rd execution", not "refuse after". Blocking would prevent the SOP from being written at all, which defeats the purpose.

## Decision 3 — purpose auto-derived from description when omitted
**Chosen:** `if not self.purpose: self.purpose = self.description` in `__post_init__`.
**Rejected:** Separate required field.
**Why:** Purpose and description often overlap for simple processes. Reduces friction without losing information.

## Decision 4 — review_date defaults to +180 days, no business-day logic
**Chosen:** `datetime.now() + timedelta(days=180)`.
**Rejected:** Calendar-aware calculation (skip weekends/holidays).
**Why:** Review dates are soft targets, not SLAs. Calendar precision adds complexity with no measurable benefit at v1.0.

## Decision 5 — Framework Library append, not overwrite
**Chosen:** `open(library_path, 'a')` — always append.
**Rejected:** Read-modify-write to deduplicate.
**Why:** Append is safe; deduplication requires parsing the library which is out of scope for Agent 0. Library management is a future Agent 1 concern.

## Decision 6 — generate_sop_filename uses regex substitution, not slugify
**Chosen:** `re.sub(r'[^a-zA-Z0-9\-_]', '_', name.lower())`
**Rejected:** External `python-slugify` dependency.
**Why:** Zero external dependencies; behaviour is explicit and testable.

## Decision 7 — Two-layer architecture (sop_writer.py + sop_writer_generator.py)
**Chosen:** Deterministic layer (dataclasses, pure functions) + dict-based wrapper for LLM use.
**Why:** Consistent with P1–P4 pattern. Wrapper accepts plain dicts, deterministic layer enforces types and gates. Both layers independently testable.
