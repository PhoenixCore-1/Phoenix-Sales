"""Persistence contract for Sales Solutions."""

from typing import Protocol
from uuid import UUID

from phoenix_sales.domain.solution import Solution


class SolutionNotFoundError(LookupError):
    """Raised when a Solution cannot be found within tenant scope."""


class SolutionRepository(Protocol):
    """Storage contract implemented by a Sales persistence adapter."""

    def save(self, solution: Solution) -> Solution: ...

    def get(self, tenant_id: str, solution_id: UUID) -> Solution | None: ...

    def list_by_opportunity(self, tenant_id: str, opportunity_id: UUID) -> list[Solution]: ...

    def delete(self, tenant_id: str, solution_id: UUID) -> None: ...
