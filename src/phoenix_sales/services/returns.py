"""Application services for Sales returns, cancellations and credits."""

from phoenix_sales.api.contracts import RequestContext
from phoenix_sales.domain.returns import CancellationRequest, CreditRequest, CreditStatus, RequestStatus, ReturnFlow, ReturnRequest
from phoenix_sales.integrations.returns import InventoryReturnAuthorisation, InventoryReturnPort, InventoryReturnResult, SageCreditPort, SageCreditRequest, SageCreditResult

class ReturnsApplicationService:
    """Coordinate commercial requests without owning inventory or accounting."""
    REQUEST_PERMISSION = "sales.returns.request"
    APPROVE_PERMISSION = "sales.returns.approve"
    CREDIT_PERMISSION = "sales.credit.request"

    def __init__(self, context: RequestContext, inventory: InventoryReturnPort, sage: SageCreditPort) -> None:
        self._context = context
        self._inventory = inventory
        self._sage = sage
        self._processed: set[str] = set()

    def request_cancellation(self, request: CancellationRequest) -> CancellationRequest:
        self._require(self.REQUEST_PERMISSION)
        self._tenant(request.tenant_id)
        return request

    def approve_return(self, request: ReturnRequest, *, item_id: str, correlation_id: str) -> InventoryReturnAuthorisation:
        self._require(self.APPROVE_PERMISSION)
        self._tenant(request.tenant_id)
        if request.status not in {RequestStatus.REQUESTED, RequestStatus.APPROVAL_REQUIRED}:
            raise ValueError("return is not awaiting approval")
        if not item_id.strip() or not correlation_id.strip():
            raise ValueError("item ID and correlation ID are required")
        ReturnFlow.validate_transition(request.status, RequestStatus.APPROVED)
        return InventoryReturnAuthorisation(request.tenant_id, request.id, request.sales_order_id, item_id, request.quantity, request.reason.value, correlation_id)

    def submit_credit(self, request: CreditRequest, *, correlation_id: str) -> SageCreditResult:
        self._require(self.CREDIT_PERMISSION)
        self._tenant(request.tenant_id)
        if request.status not in {CreditStatus.REQUESTED, CreditStatus.APPROVAL_REQUIRED, CreditStatus.APPROVED}:
            raise ValueError("credit request is not eligible for submission")
        if correlation_id in self._processed:
            raise ValueError("credit request already processed for correlation ID")
        if not correlation_id.strip():
            raise ValueError("correlation ID is required")
        result = self._sage.submit_credit(SageCreditRequest(request.tenant_id, request.id, request.sales_order_id, request.amount, request.reason, correlation_id))
        self._processed.add(correlation_id)
        return result

    def apply_inventory_result(self, request: ReturnRequest, result: InventoryReturnResult) -> ReturnRequest:
        self._require(self.APPROVE_PERMISSION)
        self._tenant(result.tenant_id)
        if result.return_request_id != request.id:
            raise ValueError("inventory result does not match return request")
        if result.received_quantity < 0 or result.received_quantity > request.quantity:
            raise ValueError("invalid received quantity")
        return ReturnRequest(request.tenant_id, request.sales_order_id, request.reason, request.quantity, request.id, RequestStatus.COMPLETED, result.inventory_reference)

    def _tenant(self, tenant_id: str) -> None:
        if tenant_id != self._context.tenant.tenant_id:
            raise PermissionError("tenant access denied")

    def _require(self, permission: str) -> None:
        if not self._context.has_permission(permission):
            raise PermissionError(f"permission denied: {permission}")
