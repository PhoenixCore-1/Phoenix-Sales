from decimal import Decimal
from uuid import uuid4

import pytest

from phoenix_sales.domain.returns import (
    CancellationRequest,
    CreditRequest,
    CreditStatus,
    RequestStatus,
    ReturnFlow,
    ReturnReason,
    ReturnRequest,
)


def test_cancellation_request_is_valid():
    request = CancellationRequest("tenant-a", uuid4(), "Customer cancelled", Decimal("5"))
    assert request.status is RequestStatus.REQUESTED
    assert request.quantity == Decimal("5")


def test_cancellation_requires_positive_quantity():
    with pytest.raises(ValueError):
        CancellationRequest("tenant-a", uuid4(), "Customer cancelled", Decimal("0"))


def test_return_request_is_valid_and_separate_from_credit():
    request = ReturnRequest("tenant-a", uuid4(), ReturnReason.WRONG_PRODUCT, Decimal("3"))
    assert request.status is RequestStatus.REQUESTED
    assert request.inventory_reference is None


def test_return_reasons_are_standardised():
    assert ReturnReason.DAMAGED.value == "DAMAGED"
    assert ReturnReason.WAREHOUSE_PICKING_ERROR.value == "WAREHOUSE_PICKING_ERROR"
    assert ReturnReason.DELIVERY_ERROR.value == "DELIVERY_ERROR"


def test_credit_can_exist_without_return():
    request = CreditRequest("tenant-a", uuid4(), Decimal("1250"), "Pricing correction")
    assert request.return_request_id is None
    assert request.status is CreditStatus.REQUESTED


def test_credit_can_link_to_return():
    return_id = uuid4()
    request = CreditRequest("tenant-a", uuid4(), Decimal("500"), "Approved return", return_request_id=return_id)
    assert request.return_request_id == return_id


def test_credit_requires_positive_amount_and_reason():
    with pytest.raises(ValueError):
        CreditRequest("tenant-a", uuid4(), Decimal("0"), "Correction")
    with pytest.raises(ValueError):
        CreditRequest("tenant-a", uuid4(), Decimal("10"), "")


def test_return_lifecycle_covers_approval_authorisation_and_inventory_receipt():
    ReturnFlow.validate_transition(RequestStatus.REQUESTED, RequestStatus.APPROVAL_REQUIRED)
    ReturnFlow.validate_transition(RequestStatus.APPROVAL_REQUIRED, RequestStatus.APPROVED)
    ReturnFlow.validate_transition(RequestStatus.APPROVED, RequestStatus.AUTHORISED)
    ReturnFlow.validate_transition(RequestStatus.AUTHORISED, RequestStatus.RECEIVED)
    ReturnFlow.validate_transition(RequestStatus.RECEIVED, RequestStatus.INSPECTING)
    ReturnFlow.validate_transition(RequestStatus.INSPECTING, RequestStatus.COMPLETED)


def test_return_lifecycle_rejects_invalid_transition():
    with pytest.raises(ValueError):
        ReturnFlow.validate_transition(RequestStatus.COMPLETED, RequestStatus.APPROVED)
