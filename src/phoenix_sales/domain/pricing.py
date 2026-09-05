"""Pricing and margin domain model for Phoenix Sales V1.0."""

from dataclasses import dataclass
from datetime import date
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
    currency: str = "ZAR"
    as_of: date | None = None

    def __post_init__(self) -> None:
        if not self.product_id.strip():
            raise ValueError("product_id is required")
        if self.quantity <= 0:
            raise ValueError("quantity must be greater than zero")
        if not self.currency.strip():
            raise ValueError("currency is required")


@dataclass(frozen=True)
class PricingRule:
    """Effective-dated selling price rule owned by Sales."""

    rule_type: PricingRuleType
    unit_price: Decimal
    priority: int
    customer_id: str | None = None
    contract_id: str | None = None
    project_id: str | None = None
    product_id: str | None = None
    currency: str = "ZAR"
    valid_from: date | None = None
    valid_to: date | None = None
    minimum_quantity: Decimal | None = None
    maximum_quantity: Decimal | None = None

    def __post_init__(self) -> None:
        if self.unit_price < 0:
            raise ValueError("unit_price cannot be negative")
        if self.priority < 0:
            raise ValueError("priority cannot be negative")
        if not self.currency.strip():
            raise ValueError("currency is required")
        if self.valid_from and self.valid_to and self.valid_to < self.valid_from:
            raise ValueError("valid_to cannot be before valid_from")
        if self.minimum_quantity is not None and self.minimum_quantity <= 0:
            raise ValueError("minimum_quantity must be greater than zero")
        if self.maximum_quantity is not None and self.maximum_quantity <= 0:
            raise ValueError("maximum_quantity must be greater than zero")
        if self.minimum_quantity is not None and self.maximum_quantity is not None and self.maximum_quantity < self.minimum_quantity:
            raise ValueError("maximum_quantity cannot be below minimum_quantity")

    def applies_to(self, context: PricingContext) -> bool:
        """Return whether this rule is applicable to the supplied context."""
        as_of = context.as_of or date.today()
        if self.product_id is not None and self.product_id != context.product_id:
            return False
        if self.currency != context.currency:
            return False
        if self.customer_id is not None and self.customer_id != context.customer_id:
            return False
        if self.contract_id is not None and self.contract_id != context.contract_id:
            return False
        if self.project_id is not None and self.project_id != context.project_id:
            return False
        if self.rule_type is PricingRuleType.RETAIL and not context.retail_customer:
            return False
        if self.valid_from and as_of < self.valid_from:
            return False
        if self.valid_to and as_of > self.valid_to:
            return False
        if self.minimum_quantity is not None and context.quantity < self.minimum_quantity:
            return False
        if self.maximum_quantity is not None and context.quantity > self.maximum_quantity:
            return False
        return True


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
    def select_applicable_rule(context: PricingContext, rules: list[PricingRule]) -> PricingRule:
        applicable = [rule for rule in rules if rule.applies_to(context)]
        if not applicable:
            raise ValueError("no applicable pricing rule found")
        return PricingEngine.select_rule(applicable)

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
