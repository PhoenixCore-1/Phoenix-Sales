from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from phoenix_sales.domain.quote import Quote, QuoteLine, QuoteStatus


def quote():
    return Quote("tenant-1", "customer-1", uuid4(), "Q-0001", "ZAR", date(2026, 12, 31))


def line(discount="10"):
    return QuoteLine("P1", "Product 1", Decimal("2"), "EA", Decimal("100"), Decimal(discount), Decimal("60"))


def test_quote_defaults_to_draft_version_one():
    q = quote()
    assert q.status is QuoteStatus.DRAFT
    assert q.version == 1


def test_quote_requires_identity_and_currency():
    with pytest.raises(ValueError):
        Quote("", "customer-1", uuid4(), "Q-1", "ZAR", date(2026, 12, 31))
    with pytest.raises(ValueError):
        Quote("tenant-1", "", uuid4(), "Q-1", "ZAR", date(2026, 12, 31))
    with pytest.raises(ValueError):
        Quote("tenant-1", "customer-1", uuid4(), "", "ZAR", date(2026, 12, 31))


def test_quote_line_calculates_net_price_and_total():
    item = line("10")
    assert item.net_unit_price == Decimal("90")
    assert item.line_total == Decimal("180")


def test_quote_total_value_sums_lines():
    q = quote()
    q.add_line(line("10"))
    q.add_line(QuoteLine("P2", "Product 2", Decimal("1"), "EA", Decimal("50")))
    assert q.total_value == Decimal("230")


def test_quote_line_rejects_invalid_values():
    with pytest.raises(ValueError):
        QuoteLine("P1", "Product", Decimal("0"), "EA", Decimal("10"))
    with pytest.raises(ValueError):
        QuoteLine("P1", "Product", Decimal("1"), "EA", Decimal("10"), Decimal("101"))
    with pytest.raises(ValueError):
        QuoteLine("P1", "Product", Decimal("1"), "EA", Decimal("-1"))


def test_locked_quote_cannot_add_lines():
    q = quote()
    q.status = QuoteStatus.APPROVED
    with pytest.raises(ValueError, match="locked"):
        q.add_line(line())


def test_customer_and_solution_links_are_supported():
    solution_id = uuid4()
    q = Quote(
        "tenant-1", "customer-1", uuid4(), "Q-0002", "ZAR", date(2026, 12, 31),
        contact_id="contact-1", project_id="project-1", solution_id=solution_id,
    )
    assert q.contact_id == "contact-1"
    assert q.project_id == "project-1"
    assert q.solution_id == solution_id
