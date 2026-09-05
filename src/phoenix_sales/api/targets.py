"""Application commands and queries for Sales Targets."""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from phoenix_sales.domain.target import SalesTarget, TargetScopeType
from phoenix_sales.services.target import SalesTargetService


@dataclass(frozen=True)
class CreateSalesTargetCommand:
    target: SalesTarget

@dataclass(frozen=True)
class GetSalesTargetQuery:
    target_id: UUID

@dataclass(frozen=True)
class UpdateSalesTargetCommand:
    target_id: UUID
    changes: dict[str, object]

@dataclass(frozen=True)
class ApproveSalesTargetCommand:
    target_id: UUID

@dataclass(frozen=True)
class ActivateSalesTargetCommand:
    target_id: UUID

@dataclass(frozen=True)
class CloseSalesTargetCommand:
    target_id: UUID

@dataclass(frozen=True)
class CancelSalesTargetCommand:
    target_id: UUID

class SalesTargetApplication:
    def __init__(self, service: SalesTargetService) -> None:
        self.service = service

    def create(self, command: CreateSalesTargetCommand) -> SalesTarget:
        return self.service.create(command.target)

    def get(self, query: GetSalesTargetQuery) -> SalesTarget:
        return self.service.get(query.target_id)

    def update(self, command: UpdateSalesTargetCommand) -> SalesTarget:
        return self.service.update(command.target_id, **command.changes)

    def approve(self, command: ApproveSalesTargetCommand) -> SalesTarget:
        return self.service.approve(command.target_id)

    def activate(self, command: ActivateSalesTargetCommand) -> SalesTarget:
        return self.service.activate(command.target_id)

    def close(self, command: CloseSalesTargetCommand) -> SalesTarget:
        return self.service.close(command.target_id)

    def cancel(self, command: CancelSalesTargetCommand) -> SalesTarget:
        return self.service.cancel(command.target_id)

    def by_scope(self, scope_type: TargetScopeType, scope_id: str) -> list[SalesTarget]:
        return self.service.list_by_scope(scope_type, scope_id)

    def by_period(self, period_start: date, period_end: date) -> list[SalesTarget]:
        return self.service.list_by_period(period_start, period_end)
