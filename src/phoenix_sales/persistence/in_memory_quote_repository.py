"""In-memory tenant-scoped Quote repository for tests."""

from uuid import UUID

from phoenix_sales.domain.quote import Quote


class InMemoryQuoteRepository:
    def __init__(self) -> None:
        self._quotes: dict[tuple[str, UUID], Quote] = {}

    def save(self, quote: Quote) -> Quote:
        self._quotes[(quote.tenant_id, quote.id)] = quote
        return quote

    def get(self, tenant_id: str, quote_id: UUID) -> Quote | None:
        return self._quotes.get((tenant_id, quote_id))

    def list_by_customer(self, tenant_id: str, customer_id: str) -> list[Quote]:
        return [q for (tenant, _), q in self._quotes.items() if tenant == tenant_id and q.customer_id == customer_id]

    def list_by_opportunity(self, tenant_id: str, opportunity_id: UUID) -> list[Quote]:
        return [q for (tenant, _), q in self._quotes.items() if tenant == tenant_id and q.opportunity_id == opportunity_id]

    def delete(self, tenant_id: str, quote_id: UUID) -> None:
        self._quotes.pop((tenant_id, quote_id), None)
