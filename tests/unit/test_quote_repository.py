from datetime import date
from decimal import Decimal
from uuid import uuid4

from phoenix_sales.domain.quote import Quote, QuoteLine
from phoenix_sales.persistence.in_memory_quote_repository import InMemoryQuoteRepository


def quote(tenant="tenant-1", customer="customer-1", opportunity=None):
    q = Quote(tenant, customer, opportunity or uuid4(), "Q-1", "ZAR", date(2026, 12, 31))
    q.add_line(QuoteLine("P1", "Product", Decimal("1"), "EA", Decimal("100")))
    return q


def test_save_and_get_is_tenant_scoped():
    repo = InMemoryQuoteRepository()
    q = quote()
    repo.save(q)
    assert repo.get("tenant-1", q.id) is q
    assert repo.get("tenant-2", q.id) is None


def test_list_by_customer_is_tenant_scoped():
    repo = InMemoryQuoteRepository()
    repo.save(quote(customer="customer-1"))
    repo.save(quote(customer="customer-2"))
    assert len(repo.list_by_customer("tenant-1", "customer-1")) == 1


def test_list_by_opportunity():
    repo = InMemoryQuoteRepository()
    opportunity_id = uuid4()
    repo.save(quote(opportunity=opportunity_id))
    repo.save(quote(opportunity=uuid4()))
    assert len(repo.list_by_opportunity("tenant-1", opportunity_id)) == 1


def test_delete_is_tenant_scoped_and_idempotent():
    repo = InMemoryQuoteRepository()
    q = quote()
    repo.save(q)
    repo.delete("tenant-2", q.id)
    assert repo.get("tenant-1", q.id) is q
    repo.delete("tenant-1", q.id)
    assert repo.get("tenant-1", q.id) is None
    repo.delete("tenant-1", q.id)
