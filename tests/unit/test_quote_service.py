from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from phoenix_sales.api.contracts import PermissionContext, RequestContext, TenantContext, UserContext
from phoenix_sales.domain.quote import Quote, QuoteLine, QuoteStatus
from phoenix_sales.persistence.in_memory_quote_repository import InMemoryQuoteRepository
from phoenix_sales.services.quote import QuoteOutcome, QuoteService


def context(*permissions: str, tenant: str = "tenant-1") -> RequestContext:
    return RequestContext(TenantContext(tenant), UserContext("user-1"), PermissionContext(frozenset(permissions)))


def quote(tenant: str = "tenant-1") -> Quote:
    q = Quote(tenant, "customer-1", uuid4(), "Q-1", "ZAR", date(2026, 12, 31))
    q.add_line(QuoteLine("P1", "Product", Decimal("1"), "EA", Decimal("100")))
    return q


def service(*permissions: str, tenant: str = "tenant-1") -> QuoteService:
    return QuoteService(context(*permissions, tenant=tenant), InMemoryQuoteRepository())


def test_create_and_read_quote():
    app = service("sales.quote.create", "sales.quote.read")
    q = quote()
    app.create_quote(q)
    assert app.get_quote(q.id) is q


def test_create_requires_line():
    app = service("sales.quote.create")
    q = Quote("tenant-1", "customer-1", uuid4(), "Q-1", "ZAR", date(2026, 12, 31))
    with pytest.raises(ValueError, match="at least one line"):
        app.create_quote(q)


def test_update_and_add_line_require_update_permission():
    app = service("sales.quote.create", "sales.quote.update")
    q = quote()
    app.create_quote(q)
    app.update_quote(q.id, payment_terms="30 days")
    app.add_line(q.id, QuoteLine("P2", "Product 2", Decimal("2"), "EA", Decimal("20")))
    assert q.payment_terms == "30 days"
    assert len(q.lines) == 2


def test_protected_fields_cannot_be_updated():
    app = service("sales.quote.create", "sales.quote.update")
    q = quote()
    app.create_quote(q)
    with pytest.raises(ValueError, match="protected"):
        app.update_quote(q.id, status=QuoteStatus.SENT)


def test_lifecycle_transition_requires_permission():
    app = service("sales.quote.create")
    q = quote()
    app.create_quote(q)
    with pytest.raises(PermissionError):
        app.transition(q.id, QuoteStatus.INTERNAL_REVIEW)


def test_quote_can_progress_to_sent():
    app = service("sales.quote.create", "sales.quote.read", "sales.quote.transition")
    q = quote()
    app.create_quote(q)
    app.transition(q.id, QuoteStatus.INTERNAL_REVIEW)
    app.transition(q.id, QuoteStatus.APPROVED)
    app.transition(q.id, QuoteStatus.SENT)
    assert app.get_quote(q.id).status is QuoteStatus.SENT


def test_rejected_and_cancelled_can_capture_reason():
    app = service("sales.quote.create", "sales.quote.read", "sales.quote.transition")
    q = quote()
    app.create_quote(q)
    app.transition(q.id, QuoteStatus.INTERNAL_REVIEW)
    app.transition(q.id, QuoteStatus.CANCELLED, QuoteOutcome("customer withdrew"))
    assert app.get_quote(q.id).status is QuoteStatus.CANCELLED


def test_cross_tenant_quote_is_not_readable():
    app = service("sales.quote.create", "sales.quote.read", tenant="tenant-1")
    q = quote("tenant-2")
    with pytest.raises(PermissionError):
        app.create_quote(q)


def test_locked_quote_cannot_be_updated():
    app = service("sales.quote.create", "sales.quote.update", "sales.quote.transition")
    q = quote()
    app.create_quote(q)
    app.transition(q.id, QuoteStatus.INTERNAL_REVIEW)
    app.transition(q.id, QuoteStatus.APPROVED)
    with pytest.raises(ValueError, match="locked"):
        app.update_quote(q.id, payment_terms="60 days")


def test_service_reads_from_repository_after_save():
    repository = InMemoryQuoteRepository()
    app = QuoteService(context("sales.quote.create", "sales.quote.read"), repository)
    q = quote()
    app.create_quote(q)
    assert repository.get("tenant-1", q.id) is q
    assert app.get_quote(q.id) is q
