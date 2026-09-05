"""Persistence contract for Sales Quotes."""

from typing import Protocol
from uuid import UUID

from phoenix_sales.domain.quote import Quote


class QuoteNotFoundError(LookupError):
    """Raised when a quote cannot be found within tenant scope."""


class QuoteRepository(Protocol):
    def save(self, quote: Quote) -> Quote: ...
    def get(self, tenant_id: str, quote_id: UUID) -> Quote | None: ...
    def list_by_customer(self, tenant_id: str, customer_id: str) -> list[Quote]: ...
    def list_by_opportunity(self, tenant_id: str, opportunity_id: UUID) -> list[Quote]: ...
    def delete(self, tenant_id: str, quote_id: UUID) -> None: ...
