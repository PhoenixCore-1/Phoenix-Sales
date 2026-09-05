"""Application boundary for Phoenix Sales Orders V1.0."""

from dataclasses import dataclass
from uuid import UUID

from phoenix_sales.api.contracts import RequestContext
from phoenix_sales.domain.sales_order import SalesOrder, SalesOrderLine, SalesOrderStatus
from phoenix_sales.services.sales_order import SalesOrderService


@dataclass(frozen=True)
class CreateSalesOrderCommand:
    order: SalesOrder


@dataclass(frozen=True)
class GetSalesOrderQuery:
    order_id: UUID


@dataclass(frozen=True)
class UpdateSalesOrderCommand:
    order_id: UUID
    changes: dict[str, object]


@dataclass(frozen=True)
class AddSalesOrderLineCommand:
    order_id: UUID
    line: SalesOrderLine


@dataclass(frozen=True)
class TransitionSalesOrderCommand:
    order_id: UUID
    target: SalesOrderStatus


class SalesOrderApplication:
    """Expose typed commands and queries without exposing persistence to callers."""

    def __init__(self, context: RequestContext, service: SalesOrderService) -> None:
        self._service = service

    def create(self, command: CreateSalesOrderCommand) -> SalesOrder:
        return self._service.create_order(command.order)

    def get(self, query: GetSalesOrderQuery) -> SalesOrder | None:
        return self._service.get_order(query.order_id)

    def update(self, command: UpdateSalesOrderCommand) -> SalesOrder:
        return self._service.update_order(command.order_id, **command.changes)

    def add_line(self, command: AddSalesOrderLineCommand) -> SalesOrder:
        return self._service.add_line(command.order_id, command.line)

    def transition(self, command: TransitionSalesOrderCommand) -> SalesOrder:
        return self._service.transition(command.order_id, command.target)
