import sqlite3
from datetime import date
from decimal import Decimal
from uuid import uuid4

from phoenix_sales.domain.quote import Quote, QuoteLine, QuoteStatus
from phoenix_sales.persistence.sqlite_quote_repository import SQLiteQuoteRepository


def make_quote(tenant="tenant-1", customer="customer-1", opportunity=None):
    q = Quote(tenant, customer, opportunity or uuid4(), "Q-100", "ZAR", date(2026, 12, 31), payment_terms="30 days")
    q.add_line(QuoteLine("P1", "Product", Decimal("2"), "EA", Decimal("100"), Decimal("5"), Decimal("60")))
    return q


def test_save_get_round_trip_including_lines():
    repo = SQLiteQuoteRepository(sqlite3.connect(":memory:"))
    q = make_quote()
    repo.save(q)
    loaded = repo.get("tenant-1", q.id)
    assert loaded is not None
    assert loaded.quote_number == q.quote_number
    assert loaded.status is QuoteStatus.DRAFT
    assert loaded.lines[0].quantity == Decimal("2")
    assert loaded.lines[0].unit_cost == Decimal("60")
    assert loaded.total_value == Decimal("190")


def test_get_is_tenant_scoped():
    repo = SQLiteQuoteRepository(sqlite3.connect(":memory:"))
    q = make_quote()
    repo.save(q)
    assert repo.get("tenant-2", q.id) is None


def test_list_by_customer_and_opportunity_are_scoped():
    repo = SQLiteQuoteRepository(sqlite3.connect(":memory:"))
    opportunity = uuid4()
    repo.save(make_quote(customer="customer-1", opportunity=opportunity))
    repo.save(make_quote(customer="customer-2", opportunity=uuid4()))
    assert len(repo.list_by_customer("tenant-1", "customer-1")) == 1
    assert len(repo.list_by_opportunity("tenant-1", opportunity)) == 1
    assert repo.list_by_customer("tenant-2", "customer-1") == []


def test_save_replaces_lines_and_updates_quote():
    repo = SQLiteQuoteRepository(sqlite3.connect(":memory:"))
    q = make_quote()
    repo.save(q)
    q.lines.clear()
    q.add_line(QuoteLine("P2", "Replacement", Decimal("1"), "EA", Decimal("50")))
    q.status = QuoteStatus.SENT
    repo.save(q)
    loaded = repo.get("tenant-1", q.id)
    assert loaded is not None
    assert loaded.status is QuoteStatus.SENT
    assert len(loaded.lines) == 1
    assert loaded.lines[0].item_id == "P2"


def test_delete_is_tenant_scoped_and_idempotent():
    repo = SQLiteQuoteRepository(sqlite3.connect(":memory:"))
    q = make_quote()
    repo.save(q)
    repo.delete("tenant-2", q.id)
    assert repo.get("tenant-1", q.id) is not None
    repo.delete("tenant-1", q.id)
    assert repo.get("tenant-1", q.id) is None
    repo.delete("tenant-1", q.id)
