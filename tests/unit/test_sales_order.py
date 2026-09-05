from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from phoenix_sales.domain.sales_order import SalesOrder, SalesOrderLine, SalesOrderStatus
from phoenix_sales.domain.sales_order_lifecycle import can_transition, validate_transition


def line(**kwargs):
    values = dict(
        item_id="ITEM-1",
        description="Test item",
        quantity=Decimal("10"),
        unit="ea",
        unit_price=Decimal("100"),
    )
    values.update(kwargs)
    return SalesOrderLine(**values)


def order(**kwargs):
    values = dict(
        tenant_id="tenant-1",
        customer_id="customer-1",
        order_number="SO-100",
        currency="ZAR",
        order_date=date(2026, 9, 5),
    )
    values.update(kwargs)
    return SalesOrder(**values)


def test_creates_sales_order():
    so = order()
    assert so.status is SalesOrderStatus.DRAFT
    assert so.total_value == Decimal("0")


def test_quote_link_requires_version():
    with pytest.raises(ValueError, match="quote_version"):
        order(quote_id=uuid4())


def test_quote_version_must_be_positive():
    with pytest.raises(ValueError, match="at least 1"):
        order(quote_id=uuid4(), quote_version=0)


def test_branch_cannot_be_blank():
    with pytest.raises(ValueError, match="branch_id"):
        order(branch_id=" ")


def test_add_line_and_total():
    so = order()
    so.add_line(line())
    assert so.total_value == Decimal("1000")


def test_discount_calculates_net_total():
    so = order()
    so.add_line(line(discount_percent=Decimal("10")))
    assert so.total_value == Decimal("900")


def test_quantity_must_be_positive():
    with pytest.raises(ValueError, match="quantity"):
        line(quantity=Decimal("0"))


def test_negative_price_rejected():
    with pytest.raises(ValueError, match="unit_price"):
        line(unit_price=Decimal("-1"))


def test_invalid_discount_rejected():
    with pytest.raises(ValueError, match="discount_percent"):
        line(discount_percent=Decimal("101"))


def test_fulfilment_quantities_cannot_exceed_ordered():
    with pytest.raises(ValueError, match="exceed"):
        line(fulfilled_quantity=Decimal("11"))


def test_negative_fulfilment_rejected():
    with pytest.raises(ValueError, match="negative"):
        line(allocated_quantity=Decimal("-1"))


def test_locked_order_cannot_add_line():
    so = order(status=SalesOrderStatus.CONFIRMED)
    with pytest.raises(ValueError, match="locked"):
        so.add_line(line())


def test_lifecycle_allowed_transitions():
    assert can_transition(SalesOrderStatus.DRAFT, SalesOrderStatus.CONFIRMED)
    assert can_transition(SalesOrderStatus.CONFIRMED, SalesOrderStatus.IN_PROCESS)
    assert can_transition(SalesOrderStatus.IN_PROCESS, SalesOrderStatus.PARTIALLY_FULFILLED)
    assert can_transition(SalesOrderStatus.PARTIALLY_FULFILLED, SalesOrderStatus.FULFILLED)
    assert can_transition(SalesOrderStatus.FULFILLED, SalesOrderStatus.CLOSED)


def test_lifecycle_rejects_invalid_transition():
    assert not can_transition(SalesOrderStatus.DRAFT, SalesOrderStatus.FULFILLED)
    with pytest.raises(ValueError, match="invalid sales order transition"):
        validate_transition(SalesOrderStatus.DRAFT, SalesOrderStatus.FULFILLED)


def test_terminal_closed_has_no_transitions():
    assert not can_transition(SalesOrderStatus.CLOSED, SalesOrderStatus.IN_PROCESS)


def test_terminal_cancelled_has_no_transitions():
    assert not can_transition(SalesOrderStatus.CANCELLED, SalesOrderStatus.CONFIRMED)


def test_backorder_can_return_to_processing():
    assert can_transition(SalesOrderStatus.BACKORDER, SalesOrderStatus.IN_PROCESS)


def test_partial_cancel_can_close_after_fulfilment():
    assert can_transition(SalesOrderStatus.PARTIALLY_CANCELLED, SalesOrderStatus.CLOSED)
