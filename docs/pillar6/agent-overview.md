# Agent Overview — Pillar 6: Finance & Commercial

## Purpose
Automate invoicing and cash flow monitoring for a solo operator. There is no cash buffer — every day a receivable sits uncollected is a risk to the business.

## Agent 0: Invoicing & Cash Flow Tracker

**Role:** Issue invoice records, track debtor days, flag overdue status, and escalate via chasing protocol.

**Non-negotiable constraints:**
- Net 14 payment terms on all engagements — no exceptions
- Debtor Days ≤ 14 at all times
- Any receivable >21 days triggers formal chasing protocol

**Inputs:**
| Field | Type | Required |
|-------|------|----------|
| client_name | str | Yes (G1) |
| engagement_name | str | Yes (G2) |
| invoice_date | str (YYYY-MM-DD) | Yes (G3) |
| amount | float > 0 | Yes (G4) |
| payment_terms_days | int | No (default: 14) |
| paid_date | str (YYYY-MM-DD) | No |
| currency | str | No (default: GBP) |

**Outputs:**
- Invoice record with status, due date, debtor days, chasing action
- Summary report across a portfolio of invoices

**Chasing Protocol:**
| Days Since Invoice | Action |
|--------------------|--------|
| ≤ 21 | None |
| > 21 | Email |
| > 25 | Call |
| > 30 | Final Notice |

**Defect Codes:**
| Code | Description |
|------|-------------|
| F1 | Invoice issued but not logged |
| F2 | Overdue invoice not chased |
| F3 | Debtor days not tracked |
