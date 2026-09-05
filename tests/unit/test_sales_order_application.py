from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from phoenix_sales.api.contracts import EntitlementContext, PermissionContext, RequestContext, TenantContext, UserContext
from phoenix_sales.api.sales_orders import (
    AddSalesOrderLineCommand,
    CreateSalesOrderCommand,
    GetSalesOrderQuery,
    SalesOrderApplication,
    TransitionSalesOrderCommand,
    UpdateSalesOrderCommand,
)
from phoenix_sales.domain.sales_order import SalesOrder, SalesOrderLine, SalesOrderStatus
from phoenix_sales.persistence.in_memory_sales_order_repository import InMemorySalesOrderRepository
from phoenix_sales.services.sales_order import SalesOrderService


def context(*permissions):
    return RequestContext(
        tenant=TenantContext("tenant-1"),
        user=UserContext("user-1"),
        permissions=PermissionContext(frozenset(permissions)),
        entitlements=EntitlementContext(frozenset()),
    )


def order():
    return SalesOrder(
        tenant_id="tenant-1",
        customer_id="customer-1",
        order_number="SO-APP-1",
        currency="ZAR",
        order_date=date(2026, 9, 5),
        lines=[SalesOrderLine("ITEM-1", "Item", Decimal("2"), "ea", Decimal("100"))],
    )


def app(*permissions):
    ctx = context(*permissions)
    return SalesOrderApplication(ctx, SalesOrderService(ctx, InMemorySalesOrderRepository()))


def test_create_command():
    application = app("sales.order.create")
    so = order()
    assert application.create(CreateSalesOrderCommand(so)) is so


def test_get_query():
    ctx = context("sales.order.create", "sales.order.read")
    repo = InMemorySalesOrderRepository()
    service = SalesOrderService(ctx, repo)
    application = SalesOrderApplication(ctx, service)
    so = order()
    service.create_order(so)
    assert application.get(GetSalesOrderQuery(so.id)) is so


def test_update_command():
    ctx = context("sales.order.create", "sales.order.update")
    repo = InMemorySalesOrderRepository()
    service = SalesOrderService(ctx, repo)
    application = SalesOrderApplication(ctx, service)
    so = order()
    service.create_order(so)
    result = application.update(UpdateSalesOrderCommand(so.id, {"customer_reference": "REF-1"}))
    assert result.customer_reference == "REF-1"


def test_add_line_command():
    ctx = context("sales.order.create", "sales.order.update")
    repo = InMemorySalesOrderRepository()
    service = SalesOrderService(ctx, repo)
    application = SalesOrderApplication(ctx, service)
    so = order()
    service.create_order(so)
    application.add_line(AddSalesOrderLineCommand(so.id, SalesOrderLine("ITEM-2", "Second", Decimal("1"), "ea", Decimal("50"))))
    assert len(so.lines) == 2


def test_transition_command():
    ctx = context("sales.order.create", "sales.order.transition")
    repo = InMemorySalesOrderRepository()
    service = SalesOrderService(ctx, repo)
    application = SalesOrderApplication(ctx, service)
    so = order()
    service.create_order(so)
    result = application.transition(TransitionSalesOrderCommand(so.id, SalesOrderStatus.CONFIRMED))
    assert result.status is SalesOrderStatus.CONFIRMED


def test_boundary_does_not_bypass_service_permissions():
    application = app()
    with pytest.raises(PermissionError):
        application.create(CreateSalesOrderCommand(order()))


def test_missing_order_returns_none_for_get():
    application = app("sales.order.read")
    assert application.get(GetSalesOrderQuery(uuid4())) is None
