from datetime import date
from decimal import Decimal

import pytest

from phoenix_sales.domain.competitor_pricing import (
    CompetitorPriceObservation,
    CompetitorPricingSource,
    CompetitorPricingValidity,
)


def make(**kwargs):
    values = dict(
        tenant_id="t1",
        competitor="Competitor A",
        competitor_product="Anchor X",
        comparable_product_id="prod-1",
        competitor_price=Decimal("1200"),
        currency="ZAR",
        observed_date=date(2026, 9, 1),
    )
    values.update(kwargs)
    return CompetitorPriceObservation(**values)


def test_observation_validates_and_calculates_unit_price():
    item = make(quantity=Decimal("10"), source=CompetitorPricingSource.CUSTOMER, confidence=Decimal("90"))
    assert item.unit_price == Decimal("120")
    assert item.source is CompetitorPricingSource.CUSTOMER


def test_price_cannot_be_negative():
    with pytest.raises(ValueError):
        make(competitor_price=Decimal("-1"))


def test_quantity_must_be_positive():
    with pytest.raises(ValueError):
        make(quantity=Decimal("0"))


def test_confidence_is_bounded():
    with pytest.raises(ValueError):
        make(confidence=Decimal("101"))


def test_required_identity_fields():
    with pytest.raises(ValueError):
        make(competitor="")
    with pytest.raises(ValueError):
        make(competitor_product="")
    with pytest.raises(ValueError):
        make(comparable_product_id="")


def test_currency_required():
    with pytest.raises(ValueError):
        make(currency="")


def test_validity_can_be_explicit():
    item = make(validity=CompetitorPricingValidity.CURRENT)
    assert item.validity is CompetitorPricingValidity.CURRENT
