from datetime import date
from decimal import Decimal

import pytest

from phoenix_sales.domain.pricing import PricingContext, PricingEngine, PricingRule, PricingRuleType


def test_applicable_rule_respects_product_customer_and_currency():
    context = PricingContext("product-1", Decimal("5"), customer_id="customer-1", currency="ZAR")
    rules = [
        PricingRule(PricingRuleType.STANDARD, Decimal("100"), 10, product_id="product-2"),
        PricingRule(PricingRuleType.CUSTOMER, Decimal("90"), 20, product_id="product-1", customer_id="customer-1"),
        PricingRule(PricingRuleType.CONTRACT, Decimal("80"), 30, product_id="product-1", customer_id="customer-1", currency="USD"),
    ]
    assert PricingEngine.select_applicable_rule(context, rules).unit_price == Decimal("90")


def test_effective_dates_are_inclusive():
    context = PricingContext("product-1", Decimal("1"), as_of=date(2026, 9, 5))
    active = PricingRule(PricingRuleType.STANDARD, Decimal("100"), 10, product_id="product-1", valid_from=date(2026, 9, 5), valid_to=date(2026, 9, 5))
    assert active.applies_to(context)
    assert PricingEngine.select_applicable_rule(context, [active]) is active


def test_expired_and_future_rules_are_ignored():
    context = PricingContext("product-1", Decimal("1"), as_of=date(2026, 9, 5))
    expired = PricingRule(PricingRuleType.STANDARD, Decimal("80"), 30, product_id="product-1", valid_to=date(2026, 9, 4))
    future = PricingRule(PricingRuleType.STANDARD, Decimal("70"), 40, product_id="product-1", valid_from=date(2026, 9, 6))
    current = PricingRule(PricingRuleType.STANDARD, Decimal("100"), 10, product_id="product-1")
    assert PricingEngine.select_applicable_rule(context, [expired, future, current]) is current


def test_quantity_breaks_are_respected():
    context = PricingContext("product-1", Decimal("50"))
    low = PricingRule(PricingRuleType.STANDARD, Decimal("100"), 10, product_id="product-1", maximum_quantity=Decimal("49"))
    bulk = PricingRule(PricingRuleType.STANDARD, Decimal("90"), 20, product_id="product-1", minimum_quantity=Decimal("50"))
    assert PricingEngine.select_applicable_rule(context, [low, bulk]).unit_price == Decimal("90")


def test_no_applicable_rule_is_explicit():
    context = PricingContext("product-1", Decimal("1"), customer_id="customer-1")
    customer_only = PricingRule(PricingRuleType.CUSTOMER, Decimal("90"), 20, product_id="product-1", customer_id="customer-2")
    with pytest.raises(ValueError, match="no applicable"):
        PricingEngine.select_applicable_rule(context, [customer_only])


def test_retail_rule_requires_retail_customer():
    non_retail = PricingContext("product-1", Decimal("1"), retail_customer=False)
    retail = PricingContext("product-1", Decimal("1"), retail_customer=True)
    rule = PricingRule(PricingRuleType.RETAIL, Decimal("110"), 10, product_id="product-1")
    assert not rule.applies_to(non_retail)
    assert rule.applies_to(retail)


def test_invalid_effective_range_and_quantity_range_are_rejected():
    with pytest.raises(ValueError):
        PricingRule(PricingRuleType.STANDARD, Decimal("100"), 1, valid_from=date(2026, 9, 6), valid_to=date(2026, 9, 5))
    with pytest.raises(ValueError):
        PricingRule(PricingRuleType.STANDARD, Decimal("100"), 1, minimum_quantity=Decimal("10"), maximum_quantity=Decimal("5"))
