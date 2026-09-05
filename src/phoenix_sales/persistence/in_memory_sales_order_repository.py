"""In-memory tenant-scoped Sales Order repository for tests."""

from uuid import UUID

from phoenix_sales.domain.sales_order import SalesOrder


class InMemorySalesOrderRepository:
    def __init__(self) -> None:
        self._orders: dict[tuple[str, UUID], SalesOrder] = {}

    def save(self, order: SalesOrder) -> SalesOrder:
        self._orders[(order.tenant_id, order.id)] = order
        return order

    def get(self, tenant_id: str, order_id: UUID) -> SalesOrder | None:
        return self._orders.get((tenant_id, order_id))

    def list_by_customer(self, tenant_id: str, customer_id: str) -> list[SalesOrder]:
        return [o for (tenant, _), o in self._orders.items() if tenant == tenant_id and o.customer_id == customer_id]

    def list_by_quote(self, tenant_id: str, quote_id: UUID) -> list[SalesOrder]:
        return [o for (tenant, _), o in self._orders.items() if tenant == tenant_id and o.quote_id == quote_id]

    def list_by_opportunity(self, tenant_id: str, opportunity_id: UUID) -> list[SalesOrder]:
        return [o for (tenant, _), o in self._orders.items() if tenant == tenant_id and o.opportunity_id == opportunity_id]

    def delete(self, tenant_id: str, order_id: UUID) -> None:
        self._orders.pop((tenant_id, order_id), None)
