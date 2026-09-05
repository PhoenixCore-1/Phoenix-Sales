"""Quote-to-Sales-Order conversion boundary for Phoenix Sales V1.0."""

from phoenix_sales.api.contracts import RequestContext
from phoenix_sales.domain.quote import Quote, QuoteStatus
from phoenix_sales.domain.sales_order import SalesOrder, SalesOrderLine
from phoenix_sales.persistence.sales_order_repository import SalesOrderRepository


class QuoteToOrderService:
    """Convert an accepted quote version into an immutable commercial order snapshot."""

    CREATE_PERMISSION = "sales.order.create"

    def __init__(self, context: RequestContext, repository: SalesOrderRepository) -> None:
        self._context = context
        self._repository = repository

    def convert(self, quote: Quote, *, order_number: str) -> SalesOrder:
        self._require(self.CREATE_PERMISSION)
        self._require_tenant(quote)
        if quote.status is not QuoteStatus.ACCEPTED:
            raise ValueError("only an accepted quote can be converted to a sales order")
        if not quote.lines:
            raise ValueError("accepted quote must contain at least one line")
        existing = self._repository.list_by_quote(self._context.tenant.tenant_id, quote.id)
        if existing:
            raise ValueError("sales order already exists for accepted quote")

        lines = [
            SalesOrderLine(
                item_id=line.item_id,
                description=line.description,
                quantity=line.quantity,
                unit=line.unit,
                unit_price=line.unit_price,
                discount_percent=line.discount_percent,
            )
            for line in quote.lines
        ]
        order = SalesOrder(
            tenant_id=quote.tenant_id,
            customer_id=quote.customer_id,
            order_number=order_number,
            currency=quote.currency,
            order_date=quote.valid_until,
            quote_id=quote.id,
            quote_version=quote.version,
            opportunity_id=quote.opportunity_id,
            contact_id=quote.contact_id,
            project_id=quote.project_id,
            solution_id=quote.solution_id,
            branch_id=quote.branch_id,
            payment_terms=quote.payment_terms,
            delivery_terms=quote.delivery_terms,
            customer_reference=quote.customer_reference,
            internal_reference=quote.internal_reference,
            notes=quote.notes,
            lines=lines,
        )
        return self._repository.save(order)

    def _require_tenant(self, quote: Quote) -> None:
        if quote.tenant_id != self._context.tenant.tenant_id:
            raise PermissionError("tenant access denied")

    def _require(self, permission: str) -> None:
        if not self._context.has_permission(permission):
            raise PermissionError(f"permission denied: {permission}")
