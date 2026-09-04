"""In-memory persistence adapter for Sales Solutions."""

from uuid import UUID

from phoenix_sales.domain.solution import Solution


class InMemorySolutionRepository:
    """Tenant-scoped in-memory implementation of SolutionRepository."""

    def __init__(self) -> None:
        self._items: dict[tuple[str, UUID], Solution] = {}

    def save(self, solution: Solution) -> Solution:
        self._items[(solution.tenant_id, solution.id)] = solution
        return solution

    def get(self, tenant_id: str, solution_id: UUID) -> Solution | None:
        return self._items.get((tenant_id, solution_id))

    def list_by_opportunity(self, tenant_id: str, opportunity_id: UUID) -> list[Solution]:
        return [
            solution
            for (stored_tenant, _), solution in self._items.items()
            if stored_tenant == tenant_id and solution.opportunity_id == opportunity_id
        ]

    def delete(self, tenant_id: str, solution_id: UUID) -> None:
        self._items.pop((tenant_id, solution_id), None)
