# Known Failure Modes — Pillar 1 Agentic System
# Derived from Blueprint tactics, KPI definitions, and LSS failure mode analysis.
# Every mode here has a corresponding assertion in /evals/feature-map.md.

---

## FM-01: Incomplete SIPOC Passed to CTQ Generator

**Risk:** Agent skips the SIPOC gate and generates a CTQ tree from partial or implied service knowledge.
**Impact:** CTQ requirements miss dependencies; deliverables are scoped against wrong quality targets; rework in first engagement.
**Detection:** Level 1 test — attempt CTQ generation without complete SIPOC input; assert gate blocks it.
**Control:** SIPOC completeness check (all 5 columns non-empty) is a hard precondition in code before CTQ logic executes.
**RPN (FMEA):** Severity 9 × Occurrence 5 × Detection 3 = **135** — Address before launch.

---

## FM-02: Subjective Language in CTQ or PPD Output

**Risk:** Agent produces a CTQ node or PPD quality criterion using subjective language ("good", "professional", "clear", "appropriate").
**Impact:** Quality criteria become uncheckable; First-Time Acceptance Rate metric becomes meaningless; client disputes on deliverable acceptance.
**Detection:** Level 1 test — run output through subjective language blocklist; assert zero matches.
**Control:** Post-generation validation step checks output text against blocklist before returning to user.
**Blocklist seed:** good, clear, professional, appropriate, reasonable, high quality, sufficient, adequate, timely, well-structured
**RPN:** Severity 8 × Occurrence 6 × Detection 4 = **192** — Address before launch.

---

## FM-03: CoPQ Price Recommendation Below £5k/Month Floor

**Risk:** CoPQ calculation returns a low total (e.g. small client, partial data); 10–20% pricing recommendation falls below £5,000/month.
**Impact:** Agent legitimises a sub-floor price; contradicts positioning; destroys AOV KPI from first client.
**Detection:** Level 1 test — input low CoPQ value; assert output price is always ≥£5,000/month.
**Control:** Floor enforcement is a hard-coded post-calculation gate, not a soft instruction.
**RPN:** Severity 10 × Occurrence 4 × Detection 2 = **80** — Monitor.

---

## FM-04: PPD Missing Required Field (Silent)

**Risk:** Agent generates a PPD with one or more of the six required fields missing or empty, and returns it without flagging the gap.
**Impact:** A deliverable is scoped and worked on without a complete quality standard; rework risk; PRINCE2 compliance failure.
**Detection:** Level 1 test — check PPD output structure against schema; assert all six fields are non-empty strings.
**Control:** PPD schema validation runs before quality check step; any empty field returns an error, not a partial PPD.
**RPN:** Severity 8 × Occurrence 4 × Detection 3 = **96** — Monitor.

---

## FM-05: Quality Check Skipped on PPD

**Risk:** PPD is returned to user without the self-quality-check step running. User assumes the PPD has been validated when it hasn't.
**Impact:** Defective PPDs enter the engagement; first deliverable may be rejected; First-Time Acceptance Rate KPI breached from Engagement 1.
**Detection:** Level 1 test — verify every PPD output in trace log contains `quality_check_passed` field (true or false, never absent).
**Control:** Quality check step is non-optional in the PPD generation pipeline; trace log enforces its presence.
**RPN:** Severity 8 × Occurrence 5 × Detection 3 = **120** — Address before launch.

---

## FM-06: ROI Narrative Generated Without CoPQ Anchor

**Risk:** Agent generates an ROI narrative for a proposal without a numeric CoPQ figure — using placeholder text or estimates without stated uncertainty.
**Impact:** Proposal ROI case is undefendable; prospect has no self-calculated justification; contradicts the core selling methodology.
**Detection:** Level 1 test — parse ROI narrative output; assert presence of a numeric CoPQ figure.
**Control:** ROI narrative generation requires a completed CoPQ calculation object as input; cannot be invoked independently.
**RPN:** Severity 9 × Occurrence 3 × Detection 3 = **81** — Monitor.

---

## FM-07: Partial CoPQ Presented as Complete Figure

**Risk:** User provides data for 2 of 4 CoPQ categories; agent sums the available data and presents the total without flagging missing categories.
**Impact:** Underestimated CoPQ leads to underpriced proposal; client anchor is wrong; pricing floor appears unearned.
**Detection:** Level 1 test — input partial category data; assert output includes explicit `missing_categories` field and `is_floor_estimate: true`.
**Control:** CoPQ output schema includes completeness metadata; any missing category triggers a conservative estimate flag.
**RPN:** Severity 7 × Occurrence 5 × Detection 4 = **140** — Address before launch.

---

## RPN Summary

| FM | Description | RPN | Action |
|----|-------------|-----|--------|
| FM-01 | Incomplete SIPOC → CTQ | 135 | Address before launch |
| FM-02 | Subjective language in output | 192 | Address before launch |
| FM-03 | Price below £5k floor | 80 | Monitor |
| FM-04 | PPD missing field (silent) | 96 | Monitor |
| FM-05 | Quality check skipped | 120 | Address before launch |
| FM-06 | ROI narrative without CoPQ | 81 | Monitor |
| FM-07 | Partial CoPQ as complete | 140 | Address before launch |

**RPN >150 threshold (address before launch):** FM-02 (192), FM-07 (140 — borderline, treat as pre-launch)
**RPN >300 stop-the-line:** None currently. Re-score after first integration test round.
