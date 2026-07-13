"""
Offer Menu & Price Floor – Wrapper for easy use.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from src.pillar0.offer_menu import (
    Offer,
    OfferMenu,
    VALID_FORMATS,
    VALID_ICP_FIT,
    to_yaml,
    from_yaml,
)


def create_offer(
    name: str,
    format: str,
    price_floor: float,
    price_range: Tuple[float, float],
    icp_fit: str,
    delivery_pillar: str,
    description: str,
    bundling_rules: Optional[List[str]] = None,
    discount_max: float = 10.0,
    discount_authority: str = "Owner",
) -> Offer:
    return Offer(
        name=name,
        format=format,
        price_floor=price_floor,
        price_range=price_range,
        icp_fit=icp_fit,
        delivery_pillar=delivery_pillar,
        description=description,
        bundling_rules=bundling_rules or [],
        discount_max=discount_max,
        discount_authority=discount_authority,
    )


def create_menu(offers: List[Offer], version: str = "1.0") -> OfferMenu:
    return OfferMenu(offers=offers, version=version)


def validate_proposal(menu_or_offer_name: Any, offer_name_or_fee: Any = None, proposed_fee: Optional[float] = None) -> Dict[str, Any]:
    """
    Two calling modes:
    - validate_proposal(menu, offer_name, fee) — object mode (backward-compatible)
    - validate_proposal(offer_name, fee)       — standalone/singleton mode; fail-open
    """
    if proposed_fee is None and offer_name_or_fee is not None:
        return check_price_floor(str(menu_or_offer_name), float(offer_name_or_fee), mode='proposal')
    return menu_or_offer_name.validate_proposal(offer_name_or_fee, proposed_fee)


def validate_invoice(menu_or_offer_name: Any, offer_name_or_amount: Any = None, invoice_amount: Optional[float] = None) -> Dict[str, Any]:
    """
    Two calling modes:
    - validate_invoice(menu, offer_name, amount) — object mode (backward-compatible)
    - validate_invoice(offer_name, amount)       — standalone/singleton mode; fail-open
    """
    if invoice_amount is None and offer_name_or_amount is not None:
        return check_price_floor(str(menu_or_offer_name), float(offer_name_or_amount), mode='invoice')
    return menu_or_offer_name.validate_invoice(offer_name_or_amount, invoice_amount)


def register_offer(menu: OfferMenu, offer_data: Dict[str, Any]) -> Offer:
    return menu.register_offer(offer_data)


def get_offer(menu: OfferMenu, name: str) -> Optional[Offer]:
    return menu.get_offer(name)


def get_menu_markdown(menu: OfferMenu) -> str:
    return menu.to_markdown()


def check_price_floor(
    offer_name: str,
    fee: float,
    *,
    menu: Optional[OfferMenu] = None,
    yaml_path: Optional[str] = None,
    mode: str = "proposal",
) -> Dict[str, Any]:
    """
    Cross-pillar gate: validate fee against P0 offer menu price floor.
    mode='proposal' → M1 defect (blocks). mode='invoice' → M2 defect (soft flag).
    Accepts a live OfferMenu object or a yaml_path to load from disk.
    Fail-open (pass=True) when menu not available or file not found.
    """
    if menu is None and yaml_path is not None:
        try:
            menu = from_yaml(Path(yaml_path).read_text(encoding="utf-8"))
        except Exception:
            return {"pass": True, "reason": "fail-open: menu not available", "source": "fail-open"}
    if menu is None:
        return {"pass": True, "reason": "fail-open: menu not available", "source": "fail-open"}
    if mode == "invoice":
        result = menu.validate_invoice(offer_name, fee)
    else:
        result = menu.validate_proposal(offer_name, fee)
    result["source"] = "p0_offer_menu"
    return result
