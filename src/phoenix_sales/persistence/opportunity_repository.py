"""Persistence contract for Sales opportunities."""

from typing import Protocol
from uuid import UUID

from phoenix_sales.domain.opportunity import Opportunity


class OpportunityNotFoundError(LookupError):
    """Raised when an opportunity cannot be found within the tenant scope."""


class OpportunityRepository(Protocol):
    """Storage contract implemented by a Sales persistence adapter."""

    def save(self, opportunity: Opportunity) -> Opportunity: ...

    def get(self, tenant_id: str, opportunity_id: UUID) -> Opportunity | None: ...

    def list_by_customer(self, tenant_id: str, customer_id: str) -> list[Opportunity]: ...

    def list_by_owner(self, tenant_id: str, owner_user_id: str) -> list[Opportunity]: ...

    def delete(self, tenant_id: str, opportunity_id: UUID) -> None: ...
