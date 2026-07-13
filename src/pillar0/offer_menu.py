"""
Offer Menu & Price Floor – Pillar 0, Agent 4
LSS MBB / Single Source of Truth for Offers.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
import yaml

VALID_FORMATS = ['Diagnostic', 'Retainer', 'Project', 'Workshop', 'Productised']
VALID_ICP_FIT = ['Core', 'Adjacent', 'Experimental']


@dataclass
class Offer:
    name: str
    format: str
    price_floor: float
    price_range: Tuple[float, float]
    icp_fit: str
    delivery_pillar: str
    description: str
    bundling_rules: List[str] = field(default_factory=list)
    discount_max: float = 10.0
    # Default is generic "Owner" — override in YAML or at construction time
    # with your name/team. Used in markdown reports and discount approval flow.
    discount_authority: str = "Owner"

    def __post_init__(self):
        if not self.name:
            raise ValueError("G1: name required")
        if self.format not in VALID_FORMATS:
            raise ValueError(f"G2: format must be one of {VALID_FORMATS}")
        if self.price_floor <= 0:
            raise ValueError("G3: price_floor must be > 0")
        if self.price_range[0] >= self.price_range[1]:
            raise ValueError("G4: price_range min must be < max")
        if self.icp_fit not in VALID_ICP_FIT:
            raise ValueError(f"G5: icp_fit must be one of {VALID_ICP_FIT}")
        if not self.delivery_pillar:
            raise ValueError("G6: delivery_pillar required")


@dataclass
class OfferMenu:
    offers: List[Offer]
    version: str = "1.0"
    date: str = field(default_factory=lambda: datetime.now().isoformat())
    global_discount_max: float = 10.0
    # Default is generic "Owner" — override in YAML or at construction time
    # with your name/team. Used in markdown reports and discount approval flow.
    global_discount_authority: str = "Owner"

    def get_offer(self, name: str) -> Optional[Offer]:
        for offer in self.offers:
            if offer.name == name:
                return offer
        return None

    def validate_proposal(self, offer_name: str, proposed_fee: float) -> Dict[str, Any]:
        offer = self.get_offer(offer_name)
        if not offer:
            return {"pass": False, "reason": f"Offer '{offer_name}' not found in menu"}
        if proposed_fee < offer.price_floor:
            return {"pass": False, "reason": f"Proposed fee £{proposed_fee:,.2f} below floor £{offer.price_floor:,.2f}"}
        return {"pass": True, "reason": None}

    def validate_invoice(self, offer_name: str, invoice_amount: float) -> Dict[str, Any]:
        offer = self.get_offer(offer_name)
        if not offer:
            return {"pass": False, "reason": f"Offer '{offer_name}' not found in menu"}
        if invoice_amount < offer.price_floor:
            return {"pass": False, "reason": f"Invoice £{invoice_amount:,.2f} below floor £{offer.price_floor:,.2f} – defect logged"}
        return {"pass": True, "reason": None}

    def register_offer(self, offer_data: Dict[str, Any]) -> 'Offer':
        offer = Offer(**offer_data)
        if self.get_offer(offer.name):
            raise ValueError(f"Offer '{offer.name}' already exists in menu")
        self.offers.append(offer)
        return offer

    def to_markdown(self) -> str:
        md = f"# Offer Menu – Version {self.version}\n"
        md += f"**Date: {self.date[:10]}**\n\n"
        md += "## Offers\n"
        md += "| Name | Format | Price Floor | Price Range | ICP Fit | Delivery Pillar |\n"
        md += "|------|--------|-------------|-------------|---------|-----------------|\n"
        for o in self.offers:
            md += f"| {o.name} | {o.format} | £{o.price_floor:,.0f} | £{o.price_range[0]:,.0f}–£{o.price_range[1]:,.0f} | {o.icp_fit} | {o.delivery_pillar} |\n"
        md += "\n## Discount Policy\n"
        md += f"**Max discount: {self.global_discount_max}%**\n"
        md += f"**Authorised by: {self.global_discount_authority}**\n"
        return md


def to_yaml(menu: OfferMenu) -> str:
    data = {
        "version": menu.version,
        "date": menu.date,
        "global_discount_max": menu.global_discount_max,
        "global_discount_authority": menu.global_discount_authority,
        "offers": [
            {
                "name": o.name,
                "format": o.format,
                "price_floor": o.price_floor,
                "price_range": list(o.price_range),
                "icp_fit": o.icp_fit,
                "delivery_pillar": o.delivery_pillar,
                "description": o.description,
                "bundling_rules": o.bundling_rules,
                "discount_max": o.discount_max,
                "discount_authority": o.discount_authority,
            }
            for o in menu.offers
        ],
    }
    return yaml.dump(data, default_flow_style=False, sort_keys=False)


def from_yaml(yaml_str: str) -> OfferMenu:
    data = yaml.safe_load(yaml_str)
    offers = [Offer(**o) for o in data["offers"]]
    return OfferMenu(
        offers=offers,
        version=str(data.get("version", "1.0")),
        date=str(data.get("date", datetime.now().isoformat())),
        global_discount_max=data.get("global_discount_max", 10.0),
        global_discount_authority=data.get("global_discount_authority", "Owner"),
    )
