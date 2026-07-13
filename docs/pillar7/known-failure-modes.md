# Known Failure Modes — Pillar 7

## FM-01: Whitespace-only strings bypass G1–G7
**Status:** Acceptable at v1.0
**Risk:** Low — internal tool, caller is trusted
**Mitigation:** Add .strip() check at UI/API boundary if needed

## FM-02: lessons_learned derivation uses only first item of what_worked and what_didnt
**Status:** By design
**Risk:** Low — summary only; full lists still appear in report sections
**Mitigation:** Extend _derive_lessons() to include all items if needed

## FM-03: is_overdue() uses report_date vs close_date, not today vs close_date
**Status:** Intentional — measures when the report WAS written, not current time
**Risk:** None — this is the correct comparison for L1 defect detection

## FM-04: log_to_lessons_log appends without deduplication
**Status:** By design — append-only log; same engagement can be logged multiple times
**Risk:** Low — duplicate entries if called twice
**Mitigation:** Caller must control invocation; deduplicate at read time if needed

## FM-05: sop_update_description not validated for content quality
**Status:** Acceptable at v1.0
**Risk:** Low — "Update SOP" accepted even if vague
**Mitigation:** Add minimum length check or structured format at v2.0
