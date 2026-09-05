"""Persistence boundary for Sales commissions."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from phoenix_sales.domain.commission import CommissionEntry, CommissionPlan


class CommissionRepository(Protocol):
    def save_plan(self, plan: CommissionPlan) -> None: ...
    def get_plan(self, tenant_id: str, plan_id: UUID) -> CommissionPlan | None: ...
    def list_plans(self, tenant_id: str) -> list[CommissionPlan]: ...
    def save_entry(self, entry: CommissionEntry) -> None: ...
    def get_entry(self, tenant_id: str, entry_id: UUID) -> CommissionEntry | None: ...
    def list_entries(self, tenant_id: str, salesperson_id: str | None = None) -> list[CommissionEntry]: ...


class InMemoryCommissionRepository:
    def __init__(self) -> None:
        self._plans: dict[tuple[str, UUID], CommissionPlan] = {}
        self._entries: dict[tuple[str, UUID], CommissionEntry] = {}

    def save_plan(self, plan: CommissionPlan) -> None:
        self._plans[(plan.tenant_id, plan.id)] = plan

    def get_plan(self, tenant_id: str, plan_id: UUID) -> CommissionPlan | None:
        return self._plans.get((tenant_id, plan_id))

    def list_plans(self, tenant_id: str) -> list[CommissionPlan]:
        return [p for (tenant, _), p in self._plans.items() if tenant == tenant_id]

    def save_entry(self, entry: CommissionEntry) -> None:
        self._entries[(entry.tenant_id, entry.id)] = entry

    def get_entry(self, tenant_id: str, entry_id: UUID) -> CommissionEntry | None:
        return self._entries.get((tenant_id, entry_id))

    def list_entries(self, tenant_id: str, salesperson_id: str | None = None) -> list[CommissionEntry]:
        return [e for (tenant, _), e in self._entries.items()
                if tenant == tenant_id and (salesperson_id is None or e.salesperson_id == salesperson_id)]
