# Build Decisions — Pillar 7

## BD-01: report_date stored as YYYY-MM-DD not full ISO timestamp
**Decision:** `datetime.now().strftime('%Y-%m-%d')` rather than `.isoformat()`
**Reason:** Consistent with other agents; avoids `[:10]` slicing; cleaner test assertions
**Trade-off:** Loses time-of-day precision; acceptable since this is a daily document

## BD-02: sop_update_required=True without description is a hard error
**Decision:** ValueError raised, not a warning
**Reason:** "SOP update required" without specifying what changes is a defect (L2), not a warning
**Trade-off:** Forces caller to provide description before creating report — by design

## BD-03: L1 detection threshold is strictly > 5 days (not >=)
**Decision:** `(report_d - close_d).days > days_limit`
**Reason:** Report on day 5 is the last acceptable day; > 5 catches day 6 onwards
**Trade-off:** Day 5 = no warning even though it's the last acceptable day

## BD-04: Lessons log entries use plain text, not markdown bold markers
**Decision:** `SOP update: No` not `**SOP update:** No`
**Reason:** Internal log format; plain text is easier to parse and search
**Trade-off:** Less visually structured than the client-facing report

## BD-05: days_since_close() is separate from is_overdue()
**Decision:** Two separate methods
**Reason:** days_since_close() is general-purpose (usable for any date); is_overdue() is the L1 business rule
**Trade-off:** Slight redundancy; justified by testability of each concern independently
