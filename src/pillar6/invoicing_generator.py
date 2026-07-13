"""
Invoicing & Cash Flow Tracker – Wrapper for easy use.
"""

from typing import List, Optional
from src.pillar6.invoicing import (
    Invoice,
    compute_summary,
    generate_invoice_report,
    generate_summary_report,
)


def create_invoice(
    client_name: str,
    engagement_name: str,
    invoice_date: str,
    amount: float,
    payment_terms_days: int = 14,
    paid_date: Optional[str] = None,
    currency: str = "GBP",
) -> Invoice:
    return Invoice(
        client_name=client_name,
        engagement_name=engagement_name,
        invoice_date=invoice_date,
        amount=amount,
        payment_terms_days=payment_terms_days,
        paid_date=paid_date,
        currency=currency,
    )


def mark_paid(invoice: Invoice, paid_date: str) -> Invoice:
    invoice.paid_date = paid_date
    invoice._compute_status()
    return invoice


def get_invoice_report(invoice: Invoice) -> str:
    return generate_invoice_report(invoice)


def get_summary_report(invoices: List[Invoice]) -> str:
    return generate_summary_report(invoices)
