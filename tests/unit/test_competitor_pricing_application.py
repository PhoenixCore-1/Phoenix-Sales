from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from phoenix_sales.api.competitor_pricing import CreateCompetitorPricingCommand, CompetitorPricingApplication, GetCompetitorPricingQuery, ListCompetitorPricingQuery, UpdateCompetitorPricingCommand
from phoenix_sales.api.contracts import PermissionContext, RequestContext, TenantContext, UserContext
from phoenix_sales.domain.competitor_pricing import CompetitorPriceObservation
from phoenix_sales.persistence.competitor_pricing_repository import InMemoryCompetitorPricingRepository
from phoenix_sales.services.competitor_pricing import CompetitorPricingService


def ctx(*permissions: str, tenant: str = "t1"):
    return RequestContext(TenantContext(tenant), UserContext("u1"), PermissionContext(frozenset(permissions)))


def item(**changes):
    values = dict(tenant_id="t1", competitor="Competitor A", competitor_product="Anchor X", comparable_product_id="prod-1", competitor_price=Decimal("1200"), currency="ZAR", observed_date=date(2026, 9, 1), customer_id="c1", project_id="p1")
    values.update(changes)
    return CompetitorPriceObservation(**values)


def app(*permissions):
    return CompetitorPricingApplication(CompetitorPricingService(ctx(*permissions), InMemoryCompetitorPricingRepository()))


def test_create_get_and_list():
    application = app("sales.competitor_pricing.create", "sales.competitor_pricing.read")
    observation = item()
    application.create(CreateCompetitorPricingCommand(observation))
    assert application.get(GetCompetitorPricingQuery(observation.id)) is observation
    assert application.list(ListCompetitorPricingQuery(competitor="Competitor A")) == [observation]
    assert application.list(ListCompetitorPricingQuery(comparable_product_id="prod-1", customer_id="c1", project_id="p1")) == [observation]


def test_date_filtering():
    repository = InMemoryCompetitorPricingRepository()
    repository.save(item(observed_date=date(2026, 9, 1)))
    assert len(repository.list("t1", observed_from=date(2026, 9, 1), observed_to=date(2026, 9, 1))) == 1
    assert repository.list("t1", observed_from=date(2026, 9, 2)) == []


def test_permissions_are_enforced():
    observation = item()
    with pytest.raises(PermissionError):
        app().create(CreateCompetitorPricingCommand(observation))


def test_cross_tenant_write_is_rejected():
    application = app("sales.competitor_pricing.create")
    with pytest.raises(PermissionError):
        application.create(CreateCompetitorPricingCommand(item(tenant_id="t2")))


def test_update_and_protected_fields():
    repository = InMemoryCompetitorPricingRepository()
    service = CompetitorPricingService(ctx("sales.competitor_pricing.create", "sales.competitor_pricing.read", "sales.competitor_pricing.update"), repository)
    observation = item()
    service.create(observation)
    service.update(observation.id, competitor_price=Decimal("1100"))
    assert service.get(observation.id).competitor_price == Decimal("1100")
    with pytest.raises(ValueError):
        service.update(observation.id, tenant_id="t2")


def test_invalid_date_range_rejected():
    repository = InMemoryCompetitorPricingRepository()
    with pytest.raises(ValueError):
        repository.list("t1", observed_from=date(2026, 9, 2), observed_to=date(2026, 9, 1))
