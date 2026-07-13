"""
Product Pipeline Manager – Wrapper for easy use.
"""

from typing import Optional, List
from src.pillar7.product_pipeline import ProductConcept, generate_pipeline_report


def create_product(
    name: str,
    launch_probability: float,
    projected_revenue_year1: float,
    description: Optional[str] = None,
    status: str = "Concept",
    ev_threshold: float = 15000.0,
    launch_date: Optional[str] = None,
) -> ProductConcept:
    return ProductConcept(
        name=name,
        launch_probability=launch_probability,
        projected_revenue_year1=projected_revenue_year1,
        description=description,
        status=status,
        ev_threshold=ev_threshold,
        launch_date=launch_date,
    )


def get_pipeline_report(products: List[ProductConcept]) -> str:
    return generate_pipeline_report(products)
