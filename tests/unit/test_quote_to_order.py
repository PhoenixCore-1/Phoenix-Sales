from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from phoenix_sales.api.contracts import EntitlementContext, PermissionContext, RequestContext, TenantContext, UserContext
from phoenix_sales.domain.quote import Quote, QuoteLine, QuoteStatus
from phoenix_sales.persistence.in_memory_sales_order_repository import InMemorySalesOrderRepository
from phoenix_sales.services.quote_to_order import QuoteToOrderService


def context(tenant="tenant-1", *permissions):
    return RequestContext(
        tenant=TenantContext(tenant),
        user=UserContext("user-1"),
        permissions=PermissionContext(frozenset(permissions)),
        entitlements=EntitlementContext(frozenset()),
    )


def quote(status=QuoteStatus.ACCEPTED, tenant="tenant-1"):
    return Quote(
        tenant_id=tenant,
        customer_id="customer-1",
        opportunity_id=uuid4(),
        quote_number="Q-100",
        currency="ZAR",
        valid_until=date(2026, 9, 5),
        version=2,
        status=status,
        branch_id="JHB",
        payment_terms="30 days",
        delivery_terms="Standard",
        customer_reference="PO-1",
        internal_reference="INT-1",
        notes="Accepted quote",
        lines=[QuoteLine("ITEM-1", "Test item", Decimal("10"), "ea", Decimal("100"), Decimal("5"))],
    )


def test_converts_accepted_quote():
    repo = InMemorySalesOrderRepository()
    service = QuoteToOrderService(context("tenant-1", "sales.order.create"), repo)
    order = service.convert(quote(), order_number="SO-100")
    assert order.quote_version == 2
    assert order.branch_id == "JHB"
    assert order.lines[0].quantity == Decimal("10")
    assert order.lines[0].discount_percent == Decimal("5")
    assert order.total_value == Decimal("950")


def test_rejects_non_accepted_quote():
    service = QuoteToOrderService(context("tenant-1", "sales.order.create"), InMemorySalesOrderRepository())
    with pytest.raises(ValueError, match="accepted quote"):
        service.convert(quote(QuoteStatus.SENT), order_number="SO-100")


def test_rejects_cross_tenant_quote():
    service = QuoteToOrderService(context("tenant-1", "sales.order.create"), InMemorySalesOrderRepository())
    with pytest.raises(PermissionError, match="tenant"):
        service.convert(quote(tenant="tenant-2"), order_number="SO-100")


def test_requires_create_permission():
    service = QuoteToOrderService(context(), InMemorySalesOrderRepository())
    with pytest.raises(PermissionError, match="sales.order.create"):
        service.convert(quote(), order_number="SO-100")


def test_prevents_duplicate_order_for_quote():
    repo = InMemorySalesOrderRepository()
    service = QuoteToOrderService(context("tenant-1", "sales.order.create"), repo)
    accepted_quote = quote()
    service.convert(accepted_quote, order_number="SO-100")
    with pytest.raises(ValueError, match="already exists"):
        service.convert(accepted_quote, order_number="SO-101")
