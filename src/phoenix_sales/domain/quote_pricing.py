"""Quote-line pricing evaluation for Phoenix Sales V1.0."""

from dataclasses import dataclass
from decimal import Decimal

from phoenix_sales.domain.discount import DiscountAuthority, DiscountStatus
from phoenix_sales.domain.margin import MarginRule, MarginStatus
from phoenix_sales.domain.pricing import PricingContext, PricingEngine, PricingRule


@dataclass(frozen=True)
class QuotePricingResult:
    """Complete commercial evaluation of a quote line."""

    product_id: str
    quantity: Decimal
    base_unit_price: Decimal
    discount_percent: Decimal
    unit_price: Decimal
    unit_cost: Decimal
    gross_profit: Decimal
    gross_margin_percent: Decimal
    discount_status: DiscountStatus
    margin_status: MarginStatus

    @property
    def approval_required(self) -> bool:
        return self.discount_status is DiscountStatus.APPROVAL_REQUIRED


class QuotePricingEngine:
    """Combine price selection, discount authority and margin rules."""

    @staticmethod
    def evaluate(
        *,
        context: PricingContext,
        pricing_rules: list[PricingRule],
        unit_cost: Decimal,
        discount_percent: Decimal,
        discount_authority: DiscountAuthority,
        margin_rule: MarginRule,
    ) -> QuotePricingResult:
        base_rule = PricingEngine.select_applicable_rule(context, pricing_rules)
        discount_percent = Decimal(discount_percent)
        if not Decimal("0") <= discount_percent <= Decimal("100"):
            raise ValueError("discount_percent must be between 0 and 100")

        unit_price = base_rule.unit_price * (Decimal("1") - discount_percent / Decimal("100"))
        margin = PricingEngine.calculate_margin(unit_price, unit_cost, context.quantity)
        discount_status = discount_authority.evaluate(discount_percent)
        margin_status = margin_rule.evaluate(margin.gross_margin_percent)

        return QuotePricingResult(
            product_id=context.product_id,
            quantity=context.quantity,
            base_unit_price=base_rule.unit_price,
            discount_percent=discount_percent,
            unit_price=unit_price,
            unit_cost=margin.unit_cost,
            gross_profit=margin.gross_profit,
            gross_margin_percent=margin.gross_margin_percent,
            discount_status=discount_status,
            margin_status=margin_status,
        )
