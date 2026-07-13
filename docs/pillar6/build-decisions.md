# Build Decisions — Pillar 6

## BD-01: Currency symbol mapping instead of raw code
**Decision:** Map GBP → £, USD → $, EUR → € in generate_invoice_report()
**Reason:** Spec output format uses £; client-facing reports use symbols not codes
**Trade-off:** Unknown currencies fall back to code string (acceptable)

## BD-02: Chasing protocol uses strict > not >=
**Decision:** days > 21 / > 25 / > 30 (not >=)
**Reason:** Day 21 is the last grace day — escalation begins on Day 22
**Trade-off:** Spec says "Day 21: Email" which could be read as >= 21; chose conservative interpretation

## BD-03: debtor_days() for paid invoices returns days to paid_date, not today
**Decision:** Paid invoices track how long it actually took to collect
**Reason:** Historical record of collection performance; avg_debtor_days in summary excludes paid (uses unpaid days)
**Trade-off:** avg_debtor_days only reflects currently unpaid exposure, not historical average collection time

## BD-04: status auto-computed in __post_init__
**Decision:** No separate status field passed in — always derived
**Reason:** Manual status is a defect source; derived status is always correct
**Trade-off:** Cannot set status = "issued" separately from "pending"; these are collapsed to pending

## BD-05: compute_summary() avg_debtor_days excludes paid invoices
**Decision:** Average computed only over unpaid (pending/overdue) invoices
**Reason:** Measures live exposure, not historical average
**Trade-off:** Doesn't capture historical collection efficiency; add separate metric if needed
