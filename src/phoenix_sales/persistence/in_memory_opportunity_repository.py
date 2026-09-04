"""In-memory Opportunity repository for tests and local development."""

from uuid import UUID

from phoenix_sales.domain.opportunity import Opportunity


class InMemoryOpportunityRepository:
    """Simple tenant-scoped repository implementing the storage contract."""

    def __init__(self) -> None:
        self._items: dict[tuple[str, UUID], Opportunity] = {}

    def save(self, opportunity: Opportunity) -> Opportunity:
        self._items[(opportunity.tenant_id, opportunity.id)] = opportunity
        return opportunity

    def get(self, tenant_id: str, opportunity_id: UUID) -> Opportunity | None:
        return self._items.get((tenant_id, opportunity_id))

    def list_by_customer(self, tenant_id: str, customer_id: str) -> list[Opportunity]:
        return [
            item
            for (item_tenant, _), item in self._items.items()
            if item_tenant == tenant_id and item.customer_id == customer_id
        ]

    def list_by_owner(self, tenant_id: str, owner_user_id: str) -> list[Opportunity]:
        return [
            item
            for (item_tenant, _), item in self._items.items()
            if item_tenant == tenant_id and item.owner_user_id == owner_user_id
        ]

    def delete(self, tenant_id: str, opportunity_id: UUID) -> None:
        self._items.pop((tenant_id, opportunity_id), None)
