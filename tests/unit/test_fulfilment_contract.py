from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from phoenix_sales.integrations.fulfilment import (
    FulfilmentLineRequest,
    FulfilmentLineResult,
    FulfilmentLineStatus,
    FulfilmentRequest,
    FulfilmentRequestStatus,
    FulfilmentResult,
    build_fulfilment_request,
)


def make_request_line(quantity="10"):
    return FulfilmentLineRequest(
        sales_order_line_id=uuid4(),
        item_id=uuid4(),
        ordered_quantity=Decimal(quantity),
        required_quantity=Decimal(quantity),
        unit="EA",
    )


def make_result_line():
    return FulfilmentLineResult(
        sales_order_line_id=uuid4(),
        item_id=uuid4(),
        ordered_quantity=Decimal("10"),
        required_quantity=Decimal("10"),
        available_quantity=Decimal("7"),
        allocated_quantity=Decimal("7"),
        backorder_quantity=Decimal("3"),
        status=FulfilmentLineStatus.PARTIALLY_ALLOCATED,
        expected_fulfilment_date=date(2026, 9, 10),
        inventory_reference="INV-001",
        warehouse_reference="JHB-WH-01",
    )


def test_request_carries_sales_order_and_commercial_fulfilment_context():
    order_id = uuid4()
    request = build_fulfilment_request(
        tenant_id="tenant-a",
        sales_order_id=order_id,
        order_number="SO-1001",
        lines=(make_request_line(),),
        commercial_branch_id="JHB",
        requested_delivery_date=date(2026, 9, 8),
        delivery_site="Customer Site",
        delivery_address="1 Test Street",
        priority="CUSTOMER_COMMITMENT",
        correlation_id="corr-001",
        metadata={"source": "sales"},
    )

    assert request.tenant_id == "tenant-a"
    assert request.sales_order_id == order_id
    assert request.order_number == "SO-1001"
    assert request.commercial_branch_id == "JHB"
    assert request.requested_delivery_date == date(2026, 9, 8)
    assert request.delivery_site == "Customer Site"
    assert request.delivery_address == "1 Test Street"
    assert request.priority == "CUSTOMER_COMMITMENT"
    assert request.correlation_id == "corr-001"
    assert request.metadata["source"] == "sales"


def test_request_line_supports_partial_required_quantity():
    line = FulfilmentLineRequest(
        sales_order_line_id=uuid4(),
        item_id=uuid4(),
        ordered_quantity=Decimal("20"),
        required_quantity=Decimal("12"),
        unit="EA",
    )
    assert line.required_quantity == Decimal("12")


def test_request_requires_lines_and_positive_quantities():
    with pytest.raises(ValueError):
        FulfilmentRequest(
            tenant_id="tenant-a",
            sales_order_id=uuid4(),
            order_number="SO-1001",
            lines=(),
        )

    with pytest.raises(ValueError):
        FulfilmentLineRequest(
            sales_order_line_id=uuid4(),
            item_id=uuid4(),
            ordered_quantity=Decimal("0"),
            required_quantity=Decimal("0"),
            unit="EA",
        )


def test_required_quantity_cannot_exceed_ordered_quantity():
    with pytest.raises(ValueError):
        FulfilmentLineRequest(
            sales_order_line_id=uuid4(),
            item_id=uuid4(),
            ordered_quantity=Decimal("5"),
            required_quantity=Decimal("6"),
            unit="EA",
        )


def test_result_carries_inventory_authoritative_allocation_and_backorder():
    result = FulfilmentResult(
        tenant_id="tenant-a",
        sales_order_id=uuid4(),
        status=FulfilmentRequestStatus.PARTIALLY_ALLOCATED,
        lines=(make_result_line(),),
        expected_fulfilment_date=date(2026, 9, 10),
        inventory_reference="INV-REQ-001",
        correlation_id="corr-001",
    )

    line = result.lines[0]
    assert line.available_quantity == Decimal("7")
    assert line.allocated_quantity == Decimal("7")
    assert line.backorder_quantity == Decimal("3")
    assert line.inventory_reference == "INV-001"
    assert line.warehouse_reference == "JHB-WH-01"
    assert result.status is FulfilmentRequestStatus.PARTIALLY_ALLOCATED


def test_result_rejects_over_allocation_or_excess_backorder():
    with pytest.raises(ValueError):
        FulfilmentLineResult(
            sales_order_line_id=uuid4(),
            item_id=uuid4(),
            ordered_quantity=Decimal("10"),
            required_quantity=Decimal("10"),
            available_quantity=Decimal("10"),
            allocated_quantity=Decimal("11"),
            backorder_quantity=Decimal("0"),
            status=FulfilmentLineStatus.ALLOCATED,
        )

    with pytest.raises(ValueError):
        FulfilmentLineResult(
            sales_order_line_id=uuid4(),
            item_id=uuid4(),
            ordered_quantity=Decimal("10"),
            required_quantity=Decimal("10"),
            available_quantity=Decimal("0"),
            allocated_quantity=Decimal("0"),
            backorder_quantity=Decimal("11"),
            status=FulfilmentLineStatus.BACKORDERED,
        )


def test_contract_is_immutable():
    request = build_fulfilment_request(
        tenant_id="tenant-a",
        sales_order_id=uuid4(),
        order_number="SO-1001",
        lines=(make_request_line(),),
    )

    with pytest.raises(AttributeError):
        request.order_number = "SO-1002"


def test_fulfilment_statuses_are_explicit():
    assert FulfilmentRequestStatus.REQUESTED.value == "REQUESTED"
    assert FulfilmentRequestStatus.ALLOCATED.value == "ALLOCATED"
    assert FulfilmentRequestStatus.BACKORDERED.value == "BACKORDERED"
    assert FulfilmentRequestStatus.FULFILLED.value == "FULFILLED"
    assert FulfilmentLineStatus.PARTIALLY_FULFILLED.value == "PARTIALLY_FULFILLED"
    assert FulfilmentLineStatus.UNAVAILABLE.value == "UNAVAILABLE"
