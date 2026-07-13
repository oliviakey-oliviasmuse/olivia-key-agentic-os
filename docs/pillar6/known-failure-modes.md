# Known Failure Modes — Pillar 6

## FM-01: Whitespace-only client/engagement names bypass G1/G2
**Status:** Acceptable at v1.0
**Risk:** Low — internal tool, caller is trusted
**Mitigation:** None at this layer; add `.strip()` check at UI/API boundary if needed

## FM-02: debtor_days() for future-dated invoices returns negative value
**Status:** By design — no guard added
**Risk:** Low — invoice_date should never be future-dated per workflow spec
**Mitigation:** Upstream validation at UI layer if future-dating becomes a use case

## FM-03: Chasing protocol boundary is exclusive (>21, not >=21)
**Status:** Intentional design — Day 21 is the grace day
**Risk:** One day's delay in escalation vs. spec wording "triggers at Day 21"
**Mitigation:** Documented in CLAUDE.md and CHANGELOG; spec reads as "after Day 21"

## FM-04: Multiple invoices to same client counted independently
**Status:** By design — no client-level aggregation in v1.0
**Risk:** Debtor days not aggregated across a client portfolio
**Mitigation:** Extend compute_summary() with client grouping if needed
