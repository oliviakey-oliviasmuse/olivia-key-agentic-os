# Build Decisions — Pillar 4

## Decision 1 — Two-layer architecture for Agent 1 (2026-06-17)

**Decision:** Ship two files: `control_plan.py` (deterministic, gate-enforced) and `control_plan_generator.py` (LLM-facing wrapper, dict API).

**Why:** The LLM wrapper uses a dict-based CTQ node API and naive FMEA matching (mode == ctq name). The deterministic layer uses the P1 CTQNode shape and requires explicit mapping. Keeping them separate means the testable layer stays clean and the LLM layer can evolve without affecting gates.

**Consequence:** FM-05 risk — production code could call the wrapper and bypass gates. Mitigate in v1.1 by having the wrapper call control_plan.py internally.

---

## Decision 2 — ctq_mapping=None triggers placeholder mode, not error (2026-06-17)

**Decision:** When no ctq_mapping is provided, G3 generates placeholder rows for all CTQs rather than raising an error.

**Why:** The system prompt specifies "If no FMEA link, create placeholder rows for all CTQs." This supports the LLM flow where the agent produces an initial draft without a pre-built mapping. The G3 warning flags the output as a draft.

**Consequence:** A placeholder control plan could be delivered to a client as final. FM-01 mitigates with warning. Escalate to hard block in v1.1 if this pattern is observed.

---

## Decision 3 — RPN_ANDON_THRESHOLD = 300 (≥300, not >300) (2026-06-17)

**Decision:** ANDON fires at RPN ≥ 300, aligned with P3 `proposal_builder.py`. The system prompt draft said ">300" — corrected to ≥300 for cross-pillar consistency.

**Why:** P3 already treats RPN 300 as ANDON. A different threshold in P4 would mean the same engagement risk is ANDON in the proposal stage but not in the control plan, which contradicts the "hold the gain" purpose.

---

## Decision 4 — Orphan CTQ check only in strict mode (2026-06-17)

**Decision:** `validate_ctq_coverage()` runs only when `ctq_mapping` is provided. In placeholder mode, `orphan_ctqs = []`.

**Why:** In placeholder mode, every CTQ gets a row by definition — an "orphan" has no meaning. Running the orphan check in placeholder mode would always return an empty list and add noise.
