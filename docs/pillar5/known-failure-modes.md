# Known Failure Modes — Pillar 5: Operations & Governance

## S1 — SOP written but not followed → false assurance
**Risk:** An SOP exists in the Framework Library but is not consulted before execution. The system has no mechanism to enforce reading compliance.
**Mitigation:** At trigger_count ≥ 3, ANDON warning is shown at execution time. Future Agent 1 (Compliance Checker) to verify sign-off before execution proceeds.

## S2 — SOP version not incremented correctly → confusion
**Risk:** A process changes but the SOP version stays at 1.0. `increment_version()` must be called explicitly; it is not automatic.
**Mitigation:** Change Log section in each SOP makes version history visible. Document: always call `increment_version()` before re-generating a revised SOP.

## S3 — Owner not updated → stale ownership
**Risk:** The original owner leaves or changes role; the SOP still names them as accountable.
**Mitigation:** Review date defaults to +6 months. Sign-off block includes owner name. Periodic review process (documented in SOP itself) should update owner field.

## FM-01 — Framework Library file not found at append time
**Risk:** `library_path` provided but file does not exist or path is wrong; append fails silently with a note in the markdown output.
**Status:** Handled — `generate_sop_report()` catches the exception and appends error note to returned markdown. File creation is left to caller.

## FM-02 — Keyword fields contain only whitespace
**Risk:** `process_name=' '` passes the `not self.process_name` check (non-empty string).
**Status:** Open — current validation uses truthiness check only. Whitespace-only inputs will not raise G1–G4 errors.
**Decision:** Acceptable at v1.0; add `.strip()` validation at next review if real-world inputs show this pattern.
