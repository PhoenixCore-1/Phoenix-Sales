from decimal import Decimal

import pytest

from phoenix_sales.domain.margin import MarginRule, MarginStatus


def test_margin_above_threshold_is_acceptable():
    rule = MarginRule(Decimal("20"), Decimal("30"))
    assert rule.evaluate(Decimal("35")) is MarginStatus.ACCEPTABLE


def test_margin_between_warning_and_minimum_is_warning():
    rule = MarginRule(Decimal("20"), Decimal("30"))
    assert rule.evaluate(Decimal("25")) is MarginStatus.WARNING


def test_margin_below_minimum_is_blocked():
    rule = MarginRule(Decimal("20"), Decimal("30"))
    assert rule.evaluate(Decimal("19.99")) is MarginStatus.BLOCKED


def test_exact_thresholds_have_expected_status():
    rule = MarginRule(Decimal("20"), Decimal("30"))
    assert rule.evaluate(Decimal("20")) is MarginStatus.WARNING
    assert rule.evaluate(Decimal("30")) is MarginStatus.ACCEPTABLE


def test_rule_can_be_product_or_category_scoped():
    assert MarginRule(Decimal("20"), product_id="P1").product_id == "P1"
    assert MarginRule(Decimal("20"), category_id="C1").category_id == "C1"


def test_invalid_thresholds_are_rejected():
    with pytest.raises(ValueError):
        MarginRule(Decimal("-1"))
    with pytest.raises(ValueError):
        MarginRule(Decimal("101"))


def test_warning_threshold_cannot_be_below_minimum():
    with pytest.raises(ValueError, match="below minimum"):
        MarginRule(Decimal("30"), Decimal("20"))


def test_rule_cannot_target_product_and_category():
    with pytest.raises(ValueError, match="both product and category"):
        MarginRule(Decimal("20"), product_id="P1", category_id="C1")
