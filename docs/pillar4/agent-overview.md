# Agent Overview — Pillar 4: Client Delivery & Success

## Agent 1 — Delivery Control Plan Generator

**Purpose:** Produce the Control Plan that operationalises "hold the gain" after a P3 proposal is accepted.

**Inputs:**
- CTQ nodes from P1 (`ctq.py` / `CTQNode` objects)
- FMEA results from P3 (`proposal_builder.build_fmea()` output)
- Optional: `ctq_mapping` dict linking FMEA modes to CTQ names

**Outputs:**
- `ControlPlanResult` with `control_plan`, `orphan_ctqs`, `warnings`, `andon_flags`, `gate`
- Markdown via `render_control_plan_md()`

**Operating modes:**
- Strict mode (`ctq_mapping` provided): every ACTION/ANDON item must be explicitly mapped; gates G3 and G4 enforced
- Placeholder mode (`ctq_mapping=None`): one row per CTQ with defaults; G3 fallback warning added

**Files:**
- `src/pillar4/control_plan.py` — deterministic layer (gates, dataclasses, testable)
- `src/pillar4/control_plan_generator.py` — LLM-facing wrapper (dict API, naive matching)
- `src/system_prompts/agent_control_plan.md` — system prompt v1.0

**Cross-pillar connections:**
- Consumes P1 CTQ nodes (live connection possible once P1 installed as package)
- Consumes P3 FMEA results (live connection possible once P3 installed as package)
- P0 (PID & RACI), P2 (FTA Tracker) — not yet built; stubs planned

**Test coverage:** 40 tests, 6 feature groups
