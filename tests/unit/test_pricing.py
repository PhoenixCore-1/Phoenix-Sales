from decimal import Decimal

import pytest

from phoenix_sales.domain.pricing import MarginResult, PricingEngine, PricingRule, PricingRuleType


def rule(rule_type, price, priority):
    return PricingRule(rule_type, Decimal(price), priority)


def test_select_rule_uses_highest_priority():
    selected = PricingEngine.select_rule([
        rule(PricingRuleType.STANDARD, "100", 10),
        rule(PricingRuleType.CUSTOMER, "90", 20),
        rule(PricingRuleType.CONTRACT, "80", 30),
    ])
    assert selected.unit_price == Decimal("80")


def test_select_rule_requires_rules():
    with pytest.raises(ValueError, match="at least one"):
        PricingEngine.select_rule([])


def test_margin_calculation():
    result = PricingEngine.calculate_margin(Decimal("120"), Decimal("80"), Decimal("10"))
    assert isinstance(result, MarginResult)
    assert result.gross_profit == Decimal("400")
    assert result.gross_margin_percent == Decimal("33.33333333333333333333333333")


def test_zero_revenue_margin_is_zero():
    result = PricingEngine.calculate_margin(Decimal("0"), Decimal("10"), Decimal("5"))
    assert result.gross_profit == Decimal("-50")
    assert result.gross_margin_percent == Decimal("0")


def test_negative_values_are_rejected():
    with pytest.raises(ValueError):
        PricingEngine.calculate_margin(Decimal("-1"), Decimal("1"), Decimal("1"))
    with pytest.raises(ValueError):
        PricingEngine.calculate_margin(Decimal("1"), Decimal("1"), Decimal("0"))


def test_pricing_rule_rejects_negative_price_and_priority():
    with pytest.raises(ValueError):
        rule(PricingRuleType.STANDARD, "-1", 1)
    with pytest.raises(ValueError):
        rule(PricingRuleType.STANDARD, "1", -1)
