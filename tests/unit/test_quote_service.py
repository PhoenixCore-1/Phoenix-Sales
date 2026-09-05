from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from phoenix_sales.api.contracts import PermissionContext, RequestContext, TenantContext, UserContext
from phoenix_sales.domain.quote import Quote, QuoteLine, QuoteStatus
from phoenix_sales.services.quote import QuoteOutcome, QuoteService


def context(*permissions: str, tenant: str = "tenant-1") -> RequestContext:
    return RequestContext(TenantContext(tenant), UserContext("user-1"), PermissionContext(frozenset(permissions)))


def quote(tenant: str = "tenant-1") -> Quote:
    q = Quote(tenant, "customer-1", uuid4(), "Q-1", "ZAR", date(2026, 12, 31))
    q.add_line(QuoteLine("P1", "Product", Decimal("1"), "EA", Decimal("100")))
    return q


def test_create_and_read_quote():
    service = QuoteService(context("sales.quote.create", "sales.quote.read"))
    q = quote()
    service.create_quote(q)
    assert service.get_quote(q.id) is q


def test_create_requires_line():
    service = QuoteService(context("sales.quote.create"))
    q = Quote("tenant-1", "customer-1", uuid4(), "Q-1", "ZAR", date(2026, 12, 31))
    with pytest.raises(ValueError, match="at least one line"):
        service.create_quote(q)


def test_update_and_add_line_require_update_permission():
    service = QuoteService(context("sales.quote.create", "sales.quote.update"))
    q = quote()
    service.create_quote(q)
    service.update_quote(q.id, payment_terms="30 days")
    service.add_line(q.id, QuoteLine("P2", "Product 2", Decimal("2"), "EA", Decimal("20")))
    assert q.payment_terms == "30 days"
    assert len(q.lines) == 2


def test_protected_fields_cannot_be_updated():
    service = QuoteService(context("sales.quote.create", "sales.quote.update"))
    q = quote()
    service.create_quote(q)
    with pytest.raises(ValueError, match="protected"):
        service.update_quote(q.id, status=QuoteStatus.SENT)


def test_lifecycle_transition_requires_permission():
    service = QuoteService(context("sales.quote.create"))
    q = quote()
    service.create_quote(q)
    with pytest.raises(PermissionError):
        service.transition(q.id, QuoteStatus.INTERNAL_REVIEW)


def test_quote_can_progress_to_sent():
    service = QuoteService(context("sales.quote.create", "sales.quote.transition"))
    q = quote()
    service.create_quote(q)
    service.transition(q.id, QuoteStatus.INTERNAL_REVIEW)
    service.transition(q.id, QuoteStatus.APPROVED)
    service.transition(q.id, QuoteStatus.SENT)
    assert q.status is QuoteStatus.SENT


def test_rejected_and_cancelled_can_capture_reason():
    service = QuoteService(context("sales.quote.create", "sales.quote.transition"))
    q = quote()
    service.create_quote(q)
    service.transition(q.id, QuoteStatus.INTERNAL_REVIEW)
    service.transition(q.id, QuoteStatus.CANCELLED, QuoteOutcome("customer withdrew"))
    assert q.status is QuoteStatus.CANCELLED


def test_cross_tenant_quote_is_not_readable():
    service = QuoteService(context("sales.quote.create", "sales.quote.read", tenant="tenant-1"))
    q = quote("tenant-2")
    with pytest.raises(PermissionError):
        service.create_quote(q)


def test_locked_quote_cannot_be_updated():
    service = QuoteService(context("sales.quote.create", "sales.quote.update", "sales.quote.transition"))
    q = quote()
    service.create_quote(q)
    service.transition(q.id, QuoteStatus.INTERNAL_REVIEW)
    service.transition(q.id, QuoteStatus.APPROVED)
    with pytest.raises(ValueError, match="locked"):
        service.update_quote(q.id, payment_terms="60 days")
