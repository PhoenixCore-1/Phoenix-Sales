"""Pricing and margin domain model for Phoenix Sales V1.0."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class PricingRuleType(str, Enum):
    STANDARD = "STANDARD"
    CUSTOMER = "CUSTOMER"
    CONTRACT = "CONTRACT"
    PROJECT = "PROJECT"
    SPECIAL_DEAL = "SPECIAL_DEAL"
    RETAIL = "RETAIL"


@dataclass(frozen=True)
class PricingContext:
    """Context used to select an effective selling-price rule."""

    product_id: str
    quantity: Decimal
    customer_id: str | None = None
    contract_id: str | None = None
    project_id: str | None = None
    retail_customer: bool = False

    def __post_init__(self) -> None:
        if not self.product_id.strip():
            raise ValueError("product_id is required")
        if self.quantity <= 0:
            raise ValueError("quantity must be greater than zero")


@dataclass(frozen=True)
class PricingRule:
    """Effective-dated selling price rule owned by Sales."""

    rule_type: PricingRuleType
    unit_price: Decimal
    priority: int
    customer_id: str | None = None
    contract_id: str | None = None
    project_id: str | None = None

    def __post_init__(self) -> None:
        if self.unit_price < 0:
            raise ValueError("unit_price cannot be negative")
        if self.priority < 0:
            raise ValueError("priority cannot be negative")


@dataclass(frozen=True)
class MarginResult:
    """Commercial margin calculated from selling price and authoritative cost."""

    unit_price: Decimal
    unit_cost: Decimal
    quantity: Decimal
    gross_profit: Decimal
    gross_margin_percent: Decimal


class PricingEngine:
    """Select prices and calculate margin without owning product cost."""

    @staticmethod
    def select_rule(rules: list[PricingRule]) -> PricingRule:
        if not rules:
            raise ValueError("at least one pricing rule is required")
        return max(rules, key=lambda rule: rule.priority)

    @staticmethod
    def calculate_margin(unit_price: Decimal, unit_cost: Decimal, quantity: Decimal) -> MarginResult:
        unit_price = Decimal(unit_price)
        unit_cost = Decimal(unit_cost)
        quantity = Decimal(quantity)
        if unit_price < 0 or unit_cost < 0:
            raise ValueError("price and cost cannot be negative")
        if quantity <= 0:
            raise ValueError("quantity must be greater than zero")
        gross_profit = (unit_price - unit_cost) * quantity
        revenue = unit_price * quantity
        margin = (gross_profit / revenue * Decimal("100")) if revenue else Decimal("0")
        return MarginResult(unit_price, unit_cost, quantity, gross_profit, margin)
