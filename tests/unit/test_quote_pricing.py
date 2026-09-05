from decimal import Decimal

import pytest

from phoenix_sales.domain.discount import DiscountAuthority, DiscountStatus
from phoenix_sales.domain.margin import MarginRule, MarginStatus
from phoenix_sales.domain.pricing import PricingContext, PricingRule, PricingRuleType
from phoenix_sales.domain.quote_pricing import QuotePricingEngine


def evaluate(discount="0", cost="70"):
    context = PricingContext(product_id="P1", quantity=Decimal("10"), currency="ZAR")
    rules = [PricingRule(PricingRuleType.STANDARD, Decimal("100"), 1)]
    return QuotePricingEngine.evaluate(
        context=context,
        pricing_rules=rules,
        unit_cost=Decimal(cost),
        discount_percent=Decimal(discount),
        discount_authority=DiscountAuthority(Decimal("10")),
        margin_rule=MarginRule(Decimal("20"), Decimal("30")),
    )


def test_base_price_is_used_without_discount():
    result = evaluate()
    assert result.base_unit_price == Decimal("100")
    assert result.unit_price == Decimal("100")
    assert result.discount_status is DiscountStatus.WITHIN_AUTHORITY
    assert result.margin_status is MarginStatus.ACCEPTABLE


def test_discount_reduces_selling_price_and_margin():
    result = evaluate(discount="10", cost="70")
    assert result.unit_price == Decimal("90")
    assert result.gross_margin_percent == Decimal("22.22222222222222222222222222")


def test_discount_over_authority_requires_approval():
    result = evaluate(discount="12", cost="60")
    assert result.approval_required
    assert result.discount_status is DiscountStatus.APPROVAL_REQUIRED


def test_margin_warning_is_returned():
    result = evaluate(discount="10", cost="68")
    assert result.margin_status is MarginStatus.WARNING


def test_margin_blocked_is_returned():
    result = evaluate(discount="10", cost="73")
    assert result.margin_status is MarginStatus.BLOCKED


def test_invalid_discount_is_rejected():
    with pytest.raises(ValueError):
        evaluate(discount="101")


def test_no_applicable_price_is_rejected():
    context = PricingContext(product_id="P1", quantity=Decimal("1"))
    with pytest.raises(ValueError, match="no applicable"):
        QuotePricingEngine.evaluate(
            context=context,
            pricing_rules=[],
            unit_cost=Decimal("50"),
            discount_percent=Decimal("0"),
            discount_authority=DiscountAuthority(Decimal("10")),
            margin_rule=MarginRule(Decimal("20")),
        )
