"""Application service for competitor pricing intelligence."""
from __future__ import annotations

from datetime import date
from uuid import UUID

from phoenix_sales.api.contracts import RequestContext
from phoenix_sales.domain.competitor_pricing import CompetitorPriceObservation
from phoenix_sales.persistence.competitor_pricing_repository import CompetitorPricingRepository


class CompetitorPricingService:
    CREATE = "sales.competitor_pricing.create"
    READ = "sales.competitor_pricing.read"
    UPDATE = "sales.competitor_pricing.update"

    def __init__(self, context: RequestContext, repository: CompetitorPricingRepository) -> None:
        self.context = context
        self.repository = repository

    def create(self, observation: CompetitorPriceObservation) -> CompetitorPriceObservation:
        self._require(self.CREATE)
        self._tenant(observation.tenant_id)
        if self.repository.get(observation.tenant_id, observation.id) is not None:
            raise ValueError("competitor pricing observation already exists")
        self.repository.save(observation)
        return observation

    def get(self, observation_id: UUID) -> CompetitorPriceObservation:
        self._require(self.READ)
        item = self.repository.get(self.context.tenant.tenant_id, observation_id)
        if item is None:
            raise KeyError("competitor pricing observation not found")
        return item

    def list(self, *, competitor: str | None = None, comparable_product_id: str | None = None, customer_id: str | None = None, project_id: str | None = None, observed_from: date | None = None, observed_to: date | None = None) -> list[CompetitorPriceObservation]:
        self._require(self.READ)
        return self.repository.list(self.context.tenant.tenant_id, competitor=competitor, comparable_product_id=comparable_product_id, customer_id=customer_id, project_id=project_id, observed_from=observed_from, observed_to=observed_to)

    def update(self, observation_id: UUID, **changes: object) -> CompetitorPriceObservation:
        self._require(self.UPDATE)
        item = self.get(observation_id)
        protected = {"id", "tenant_id", "created_at"}
        if protected.intersection(changes):
            raise ValueError("protected observation fields cannot be changed")
        for key, value in changes.items():
            if not hasattr(item, key):
                raise ValueError(f"unknown observation field: {key}")
            setattr(item, key, value)
        item.__post_init__()
        self.repository.save(item)
        return item

    def _tenant(self, tenant_id: str) -> None:
        if tenant_id != self.context.tenant.tenant_id:
            raise PermissionError("cross-tenant access denied")

    def _require(self, permission: str) -> None:
        if not self.context.has_permission(permission):
            raise PermissionError(f"missing permission: {permission}")
