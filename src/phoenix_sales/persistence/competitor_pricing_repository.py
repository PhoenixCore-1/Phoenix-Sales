"""Persistence boundary for competitor pricing intelligence."""
from __future__ import annotations

from datetime import date
from typing import Protocol
from uuid import UUID

from phoenix_sales.domain.competitor_pricing import CompetitorPriceObservation


class CompetitorPricingRepository(Protocol):
    def save(self, observation: CompetitorPriceObservation) -> None: ...
    def get(self, tenant_id: str, observation_id: UUID) -> CompetitorPriceObservation | None: ...
    def list(self, tenant_id: str, *, competitor: str | None = None, comparable_product_id: str | None = None, customer_id: str | None = None, project_id: str | None = None, observed_from: date | None = None, observed_to: date | None = None) -> list[CompetitorPriceObservation]: ...


class InMemoryCompetitorPricingRepository:
    def __init__(self) -> None:
        self._items: dict[tuple[str, UUID], CompetitorPriceObservation] = {}

    def save(self, observation: CompetitorPriceObservation) -> None:
        self._items[(observation.tenant_id, observation.id)] = observation

    def get(self, tenant_id: str, observation_id: UUID) -> CompetitorPriceObservation | None:
        return self._items.get((tenant_id, observation_id))

    def list(self, tenant_id: str, *, competitor: str | None = None, comparable_product_id: str | None = None, customer_id: str | None = None, project_id: str | None = None, observed_from: date | None = None, observed_to: date | None = None) -> list[CompetitorPriceObservation]:
        if observed_from and observed_to and observed_to < observed_from:
            raise ValueError("observed_to cannot be before observed_from")
        result = []
        for (tenant, _), item in self._items.items():
            if tenant != tenant_id:
                continue
            if competitor is not None and item.competitor != competitor:
                continue
            if comparable_product_id is not None and item.comparable_product_id != comparable_product_id:
                continue
            if customer_id is not None and item.customer_id != customer_id:
                continue
            if project_id is not None and item.project_id != project_id:
                continue
            if observed_from is not None and item.observed_date < observed_from:
                continue
            if observed_to is not None and item.observed_date > observed_to:
                continue
            result.append(item)
        return result
