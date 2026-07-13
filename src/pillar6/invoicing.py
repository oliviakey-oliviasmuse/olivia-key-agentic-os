"""
Invoicing & Cash Flow Tracker – Pillar 6, Agent 0
LSS MBB / Cash Flow Management.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

try:
    from src.pillar0.offer_menu_generator import check_price_floor
    _P0_AVAILABLE = True
except ImportError:
    check_price_floor = None  # type: ignore[assignment]
    _P0_AVAILABLE = False

_CURRENCY_SYMBOLS: Dict[str, str] = {'GBP': '£', 'USD': '$', 'EUR': '€'}


@dataclass
class Invoice:
    client_name: str
    engagement_name: str
    invoice_date: str
    amount: float
    payment_terms_days: int = 14
    paid_date: Optional[str] = None
    status: str = "pending"
    currency: str = "GBP"
    defect_reason: Optional[str] = None  # set by check_against_offer_menu() — M2 soft flag

    def __post_init__(self) -> None:
        if not self.client_name:
            raise ValueError("G1: client_name required")
        if not self.engagement_name:
            raise ValueError("G2: engagement_name required")
        try:
            datetime.strptime(self.invoice_date, '%Y-%m-%d')
        except ValueError:
            raise ValueError("G3: invoice_date must be YYYY-MM-DD")
        if self.amount <= 0:
            raise ValueError("G4: amount must be > 0")
        if self.paid_date:
            try:
                datetime.strptime(self.paid_date, '%Y-%m-%d')
            except ValueError:
                raise ValueError("paid_date must be YYYY-MM-DD")
        self._compute_status()

    def _compute_status(self) -> None:
        if self.paid_date:
            self.status = "paid"
            return
        if datetime.now().date() > self._due_date():
            self.status = "overdue"
        else:
            self.status = "pending"

    def _due_date(self):
        return (
            datetime.strptime(self.invoice_date, '%Y-%m-%d').date()
            + timedelta(days=self.payment_terms_days)
        )

    def due_date(self) -> str:
        return self._due_date().isoformat()

    def debtor_days(self) -> int:
        issued = datetime.strptime(self.invoice_date, '%Y-%m-%d').date()
        if self.paid_date:
            paid = datetime.strptime(self.paid_date, '%Y-%m-%d').date()
            return (paid - issued).days
        return (datetime.now().date() - issued).days

    def check_against_offer_menu(self, menu=None, yaml_path=None) -> Dict[str, Any]:
        """
        Soft M2 gate: checks invoice amount against P0 A4 offer menu price floor.
        On failure: sets self.status='defect' and self.defect_reason (invoice is NOT deleted).
        Fail-open (pass=True) when P0 unavailable or menu YAML not found.
        """
        if not _P0_AVAILABLE:
            return {"pass": True, "reason": "fail-open: P0 unavailable", "source": "fail-open"}
        if menu is None and yaml_path is None:
            return {"pass": True, "reason": "fail-open: no menu supplied", "source": "fail-open"}
        result = check_price_floor(
            self.engagement_name, self.amount,
            menu=menu, yaml_path=yaml_path, mode="invoice",
        )
        if not result["pass"]:
            self.status = "defect"
            self.defect_reason = result.get("reason", "below price floor")
        return result

    def chasing_action(self) -> str:
        if self.status == "paid":
            return "Paid"
        days = self.debtor_days()
        if days > 30:
            return "Final Notice Day 30"
        if days > 25:
            return "Call Day 25"
        if days > 21:
            return "Email Day 21"
        return "None"


def compute_summary(invoices: List[Invoice]) -> Dict[str, Any]:
    total_issued = sum(i.amount for i in invoices)
    total_paid = sum(i.amount for i in invoices if i.status == "paid")
    total_overdue = sum(i.amount for i in invoices if i.status == "overdue")
    unpaid_days = [i.debtor_days() for i in invoices if i.status != "paid"]
    avg_debtor_days = sum(unpaid_days) / len(unpaid_days) if unpaid_days else 0.0
    return {
        'total': len(invoices),
        'total_issued': total_issued,
        'total_paid': total_paid,
        'total_overdue': total_overdue,
        'avg_debtor_days': avg_debtor_days,
    }


def generate_invoice_report(invoice: Invoice) -> str:
    symbol = _CURRENCY_SYMBOLS.get(invoice.currency, invoice.currency)
    lines = [
        "# Invoice Record",
        f"**Client:** {invoice.client_name}",
        f"**Engagement:** {invoice.engagement_name}",
        f"**Invoice Date:** {invoice.invoice_date}",
        f"**Due Date:** {invoice.due_date()}",
        f"**Amount:** {symbol}{invoice.amount:,.2f}",
        f"**Status:** {invoice.status}",
        f"**Debtor Days:** {invoice.debtor_days()} days",
        f"**Chasing Protocol:** {invoice.chasing_action()}",
    ]
    return "\n".join(lines) + "\n"


def generate_summary_report(invoices: List[Invoice]) -> str:
    s = compute_summary(invoices)
    lines = [
        "## Invoice Summary",
        f"Total invoices: {s['total']}",
        f"Total issued: {s['total_issued']:,.2f}",
        f"Total paid: {s['total_paid']:,.2f}",
        f"Total overdue: {s['total_overdue']:,.2f}",
        f"Average debtor days: {s['avg_debtor_days']:.1f}",
    ]
    return "\n".join(lines) + "\n"
