from decimal import Decimal
from uuid import uuid4

import pytest

from phoenix_sales.api.contracts import EntitlementContext, PermissionContext, RequestContext, TenantContext, UserContext
from phoenix_sales.domain.returns import CancellationRequest, CreditRequest, CreditStatus, ReturnReason, ReturnRequest
from phoenix_sales.integrations.returns import InventoryReturnResult, SageCreditResult
from phoenix_sales.services.returns import ReturnsApplicationService


class InventoryStub:
    def authorise_return(self, request):
        return InventoryReturnResult(request.tenant_id, request.return_request_id, "RET-1", request.quantity, "QUARANTINE", request.correlation_id)


class SageStub:
    def submit_credit(self, request):
        return SageCreditResult(request.tenant_id, request.credit_request_id, "CONFIRMED", "CN-1", request.correlation_id)


def context(*permissions):
    return RequestContext(TenantContext("tenant-a"), UserContext("user-a"), PermissionContext(frozenset(permissions)), EntitlementContext(frozenset()))


def test_cancellation_requires_permission_and_preserves_request():
    service = ReturnsApplicationService(context("sales.returns.request"), InventoryStub(), SageStub())
    request = CancellationRequest("tenant-a", uuid4(), "Customer cancelled", Decimal("2"))
    assert service.request_cancellation(request) is request


def test_return_approval_creates_inventory_boundary():
    service = ReturnsApplicationService(context("sales.returns.approve"), InventoryStub(), SageStub())
    request = ReturnRequest("tenant-a", uuid4(), ReturnReason.DAMAGED, Decimal("3"))
    auth = service.approve_return(request, item_id="ITEM-1", correlation_id="corr-1")
    assert auth.return_request_id == request.id
    assert auth.item_id == "ITEM-1"
    assert auth.quantity == Decimal("3")


def test_inventory_result_completes_return_without_sales_inventory_control():
    service = ReturnsApplicationService(context("sales.returns.approve"), InventoryStub(), SageStub())
    request = ReturnRequest("tenant-a", uuid4(), ReturnReason.WRONG_PRODUCT, Decimal("4"))
    result = InventoryReturnResult("tenant-a", request.id, "RET-9", Decimal("4"), "AVAILABLE", "corr-9")
    completed = service.apply_inventory_result(request, result)
    assert completed.status.value == "COMPLETED"
    assert completed.inventory_reference == "RET-9"


def test_credit_submission_is_separate_from_return():
    service = ReturnsApplicationService(context("sales.credit.request"), InventoryStub(), SageStub())
    request = CreditRequest("tenant-a", uuid4(), Decimal("250"), "Pricing correction")
    result = service.submit_credit(request, correlation_id="credit-1")
    assert result.status == "CONFIRMED"
    assert result.sage_reference == "CN-1"


def test_credit_is_idempotent_by_correlation_id():
    service = ReturnsApplicationService(context("sales.credit.request"), InventoryStub(), SageStub())
    request = CreditRequest("tenant-a", uuid4(), Decimal("250"), "Correction")
    service.submit_credit(request, correlation_id="credit-1")
    with pytest.raises(ValueError):
        service.submit_credit(request, correlation_id="credit-1")


def test_cross_tenant_is_rejected():
    service = ReturnsApplicationService(context("sales.returns.request"), InventoryStub(), SageStub())
    request = CancellationRequest("tenant-b", uuid4(), "Cancelled", Decimal("1"))
    with pytest.raises(PermissionError):
        service.request_cancellation(request)


def test_missing_permission_is_rejected():
    service = ReturnsApplicationService(context(), InventoryStub(), SageStub())
    request = CancellationRequest("tenant-a", uuid4(), "Cancelled", Decimal("1"))
    with pytest.raises(PermissionError):
        service.request_cancellation(request)
