from decimal import Decimal
from uuid import uuid4

import pytest

from phoenix_sales.api.contracts import EntitlementContext, PermissionContext, RequestContext, TenantContext, UserContext
from phoenix_sales.domain.sales_order import SalesOrder, SalesOrderLine, SalesOrderStatus
from phoenix_sales.integrations.fulfilment import FulfilmentLineResult, FulfilmentLineStatus, FulfilmentRequest, FulfilmentRequestStatus, FulfilmentResult
from phoenix_sales.persistence.in_memory_sales_order_repository import InMemorySalesOrderRepository
from phoenix_sales.services.fulfilment_orchestration import FulfilmentOrchestrationService, sales_order_line_reference


class FakeInventory:
    def __init__(self, result=None):
        self.request = None
        self.result = result

    def submit(self, request: FulfilmentRequest):
        self.request = request
        return self.result


def context(*permissions):
    return RequestContext(
        tenant=TenantContext("tenant-a"),
        user=UserContext("user-a"),
        permissions=PermissionContext(frozenset(permissions)),
        entitlements=EntitlementContext(frozenset()),
    )


def make_order(status=SalesOrderStatus.CONFIRMED):
    return SalesOrder(
        tenant_id="tenant-a",
        customer_id="customer-a",
        order_number="SO-1001",
        currency="ZAR",
        order_date=__import__("datetime").date(2026, 9, 5),
        branch_id="JHB",
        status=status,
        lines=[SalesOrderLine("ITEM-1", "Anchor", Decimal("10"), "EA", Decimal("100"))],
    )


def make_result(order, fulfilled="0", allocated="7", backorder="3", status=FulfilmentRequestStatus.PARTIALLY_ALLOCATED, correlation="corr-1"):
    ref = sales_order_line_reference(order.id, 0)
    return FulfilmentResult(
        tenant_id=order.tenant_id,
        sales_order_id=order.id,
        status=status,
        correlation_id=correlation,
        lines=(FulfilmentLineResult(
            sales_order_line_id=ref,
            item_id="ITEM-1",
            ordered_quantity=Decimal("10"),
            required_quantity=Decimal("10"),
            available_quantity=Decimal(allocated),
            allocated_quantity=Decimal(allocated),
            fulfilled_quantity=Decimal(fulfilled),
            backorder_quantity=Decimal(backorder),
            status=FulfilmentLineStatus.PARTIALLY_ALLOCATED,
        ),),
    )


def test_request_builds_inventory_request_from_confirmed_order():
    order = make_order()
    result = make_result(order)
    inventory = FakeInventory(result)
    service = FulfilmentOrchestrationService(context("sales.order.fulfil"), InMemorySalesOrderRepository(), inventory)
    service._repository.save(order)

    service.request_fulfilment(order.id, correlation_id="corr-1", priority="CUSTOMER_COMMITMENT")

    assert inventory.request.sales_order_id == order.id
    assert inventory.request.tenant_id == "tenant-a"
    assert inventory.request.commercial_branch_id == "JHB"
    assert inventory.request.lines[0].item_id == "ITEM-1"
    assert inventory.request.lines[0].required_quantity == Decimal("10")


def test_partial_allocation_updates_order_without_owning_inventory():
    order = make_order()
    result = make_result(order)
    service = FulfilmentOrchestrationService(context("sales.order.fulfil"), InMemorySalesOrderRepository(), FakeInventory(result))
    service._repository.save(order)

    saved = service.request_fulfilment(order.id, correlation_id="corr-1")

    assert saved.lines[0].allocated_quantity == Decimal("7")
    assert saved.lines[0].backorder_quantity == Decimal("3")
    assert saved.status is SalesOrderStatus.IN_PROCESS


def test_full_fulfilment_transitions_confirmed_order_through_in_process():
    order = make_order()
    result = make_result(order, fulfilled="10", allocated="10", backorder="0", status=FulfilmentRequestStatus.FULFILLED)
    service = FulfilmentOrchestrationService(context("sales.order.fulfil"), InMemorySalesOrderRepository(), FakeInventory(result))
    service._repository.save(order)

    saved = service.request_fulfilment(order.id, correlation_id="corr-1")

    assert saved.lines[0].fulfilled_quantity == Decimal("10")
    assert saved.status is SalesOrderStatus.FULFILLED


def test_full_backorder_sets_backorder_status():
    order = make_order()
    result = make_result(order, fulfilled="0", allocated="0", backorder="10", status=FulfilmentRequestStatus.BACKORDERED)
    service = FulfilmentOrchestrationService(context("sales.order.fulfil"), InMemorySalesOrderRepository(), FakeInventory(result))
    service._repository.save(order)

    saved = service.request_fulfilment(order.id, correlation_id="corr-1")

    assert saved.status is SalesOrderStatus.BACKORDER


def test_result_can_update_only_returned_lines():
    order = make_order()
    second = SalesOrderLine("ITEM-2", "Screw", Decimal("5"), "EA", Decimal("20"))
    order.lines.append(second)
    ref = sales_order_line_reference(order.id, 0)
    result = FulfilmentResult(
        tenant_id="tenant-a", sales_order_id=order.id,
        status=FulfilmentRequestStatus.PARTIALLY_ALLOCATED,
        correlation_id="corr-1",
        lines=(FulfilmentLineResult(ref, "ITEM-1", Decimal("10"), Decimal("10"), Decimal("10"), Decimal("10"), Decimal("0"), FulfilmentLineStatus.ALLOCATED),),
    )
    repo = InMemorySalesOrderRepository(); repo.save(order)
    service = FulfilmentOrchestrationService(context("sales.order.fulfil"), repo, FakeInventory(result))

    saved = service.apply_result(result)

    assert len(saved.lines) == 2
    assert saved.lines[1].item_id == "ITEM-2"


def test_cross_tenant_result_is_rejected():
    order = make_order()
    repo = InMemorySalesOrderRepository(); repo.save(order)
    result = make_result(order)
    result = FulfilmentResult("tenant-b", order.id, result.status, result.lines, correlation_id="corr-1")
    service = FulfilmentOrchestrationService(context("sales.order.fulfil"), repo, FakeInventory())
    with pytest.raises(PermissionError):
        service.apply_result(result)


def test_permission_is_required():
    order = make_order()
    repo = InMemorySalesOrderRepository(); repo.save(order)
    service = FulfilmentOrchestrationService(context(), repo, FakeInventory())
    with pytest.raises(PermissionError):
        service.request_fulfilment(order.id)


def test_duplicate_correlation_is_rejected():
    order = make_order()
    result = make_result(order)
    inventory = FakeInventory(result)
    repo = InMemorySalesOrderRepository(); repo.save(order)
    service = FulfilmentOrchestrationService(context("sales.order.fulfil"), repo, inventory)
    service.request_fulfilment(order.id, correlation_id="corr-1")
    with pytest.raises(ValueError, match="already processed"):
        service.request_fulfilment(order.id, correlation_id="corr-1")
