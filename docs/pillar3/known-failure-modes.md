# Known Failure Modes — Pillar 3 Agentic System
# FMEA: Severity (S) × Occurrence (O) × Detectability (D) = RPN

| ID | Failure Mode | Effect | S | O | D | RPN | Mitigation |
|----|-------------|--------|---|---|---|-----|-----------|
| FM-01 | Scorecard too long — prospect abandons before completing (S1 risk) | Zero data collected; CAC reduction goal fails | 6 | 5 | 5 | 150 | Default 8 questions; S1 trigger sends one-question follow-up within 7 days |
| FM-02 | Question bank too generic — questions don't resonate with prospect's specific industry | Low completion rate; scores don't predict fit | 7 | 4 | 5 | 140 | G2 gate requires questions be industry/pain-specific; 3 separate type banks maintained |
| FM-03 | Threshold too high — qualified prospects rejected (S3 defect) | False negatives; pipeline shrinks artificially | 8 | 3 | 5 | 120 | S3 defect code tracked; 3 occurrences trigger threshold review |
| FM-04 | Threshold too low — unqualified prospects proceed to Discovery Call (S2 defect) | Wasted sales time; high CAC; poor close rate | 7 | 4 | 4 | 112 | S2 defect code tracked; 3 occurrences trigger threshold review |
| FM-05 | Scorecard scored but not logged to outreach_log.md | No follow-up trail; S2/S3 defects cannot be detected | 6 | 4 | 6 | 144 | Log entry is a required output step in agent workflow; trace.py captures every interaction |
| FM-06 | S2/S3 defects not reviewed — rubric never calibrated | Threshold stays wrong indefinitely; pattern invisible | 8 | 5 | 4 | 160 | Quarterly review of outreach_log.md mandatory; S2/S3 log entries trigger calibration prompt after 3 occurrences |
| FM-07 | Business case heuristic passes on substring false-positives (e.g. 'urgent' in 'urgency', 'capacity' in 'no capacity') | Business case PASS when criteria not genuinely met; C3 defect risk | 6 | 5 | 3 | 90 | `manual_override` flag; warning always included in output; replace with LLM-based semantic validation |

---

## Highest Priority Failure Modes (RPN ≥ 150)

1. **FM-06** (RPN 160): S2/S3 defects not reviewed. Rubric never calibrates. **Mitigation: mandatory quarterly outreach_log.md review; 3-strike threshold trigger.** Next review: 2026-09-14.
2. **FM-01** (RPN 150): Scorecard abandonment. Default 8 questions reduces burden; S1 fallback to one-question version.
3. **FM-05** (RPN 144): Missing log entry. Log step is non-optional in agent workflow.

---

## Discovery Analyser (Agent 2) – Heuristic Limitations

**Issue:** The business case validation function (`validate_business_case`) uses keyword matching as a heuristic for PRINCE2 criteria (viable, desirable, achievable).

**Known false-positives:**
- `'urgent'` matches `'urgency'` – a prospect saying "we have urgency" passes, but `'urgency'` alone is not a strong signal.
- `'capacity'` matches `'no capacity'` – a prospect saying "we have no capacity" would incorrectly pass the `achievable` check.

**Mitigation:**
- `manual_override` flag allows the user to bypass the heuristic and force a PASS (with a warning).
- The heuristic is intended as a placeholder until the LLM-based validation is implemented.
- A warning is always included in the output to remind the user to review the business case manually.

**Plan:** Replace with LLM-based semantic validation in the next major version.

---

## Threshold Calibration Trigger

If 3 × S2 defects (false positives) accumulate: review whether `threshold_pass` should be raised, or whether specific low-predictive-value questions should be removed or reweighted.

If 3 × S3 defects (false negatives) accumulate: review whether `threshold_pass` should be lowered, or whether DEFER prospects are receiving sufficient follow-up nurturing before final rejection.
