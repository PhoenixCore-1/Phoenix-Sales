"""Persistence boundary for Sales Targets."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from phoenix_sales.domain.target import SalesTarget


class SalesTargetRepository(Protocol):
    def save(self, target: SalesTarget) -> None: ...
    def get(self, tenant_id: str, target_id: UUID) -> SalesTarget | None: ...
    def list_by_scope(self, tenant_id: str, scope_type: str, scope_id: str) -> list[SalesTarget]: ...
    def list_by_period(self, tenant_id: str, period_start, period_end) -> list[SalesTarget]: ...
    def delete(self, tenant_id: str, target_id: UUID) -> None: ...


class InMemorySalesTargetRepository:
    def __init__(self) -> None:
        self._items: dict[tuple[str, UUID], SalesTarget] = {}

    def save(self, target: SalesTarget) -> None:
        self._items[(target.tenant_id, target.id)] = target

    def get(self, tenant_id: str, target_id: UUID) -> SalesTarget | None:
        return self._items.get((tenant_id, target_id))

    def list_by_scope(self, tenant_id: str, scope_type: str, scope_id: str) -> list[SalesTarget]:
        return [t for (tenant, _), t in self._items.items()
                if tenant == tenant_id and t.scope_type.value == scope_type and t.scope_id == scope_id]

    def list_by_period(self, tenant_id: str, period_start, period_end) -> list[SalesTarget]:
        return [t for (tenant, _), t in self._items.items()
                if tenant == tenant_id and t.period_start <= period_end and t.period_end >= period_start]

    def delete(self, tenant_id: str, target_id: UUID) -> None:
        self._items.pop((tenant_id, target_id), None)
