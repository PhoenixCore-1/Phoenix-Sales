import sqlite3
from datetime import date, datetime, timezone
from decimal import Decimal

from phoenix_sales.domain.opportunity import Opportunity, OpportunityStage
from phoenix_sales.persistence.sqlite_opportunity_repository import SQLiteOpportunityRepository


def make_opportunity(tenant="tenant-1", customer="customer-1", owner="user-1"):
    return Opportunity(
        tenant_id=tenant,
        name="Test opportunity",
        customer_id=customer,
        owner_user_id=owner,
        contact_id="contact-1",
        requirement="Requirement",
        application="Application",
        estimated_value=Decimal("1234.50"),
        estimated_margin=Decimal("321.25"),
        close_date=date(2026, 10, 1),
        stage=OpportunityStage.QUALIFIED,
        probability=Decimal("35.5"),
        source="CRM",
        project_id="project-1",
        competitor="Competitor A",
        current_solution="Current",
        lost_reason=None,
        outcome_reason=None,
        deferred_until=None,
        created_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 9, 2, tzinfo=timezone.utc),
    )


def test_round_trip_preserves_domain_values():
    repo = SQLiteOpportunityRepository(sqlite3.connect(":memory:"))
    item = make_opportunity()
    repo.save(item)
    loaded = repo.get(item.tenant_id, item.id)
    assert loaded == item


def test_get_is_tenant_scoped():
    repo = SQLiteOpportunityRepository(sqlite3.connect(":memory:"))
    item = make_opportunity()
    repo.save(item)
    assert repo.get("tenant-2", item.id) is None


def test_customer_and_owner_queries_are_tenant_scoped():
    repo = SQLiteOpportunityRepository(sqlite3.connect(":memory:"))
    first = make_opportunity()
    second = make_opportunity(customer="customer-2", owner="user-2")
    other = make_opportunity(tenant="tenant-2")
    for item in (first, second, other):
        repo.save(item)
    assert repo.list_by_customer("tenant-1", "customer-1") == [first]
    assert repo.list_by_owner("tenant-1", "user-1") == [first]


def test_save_updates_existing_identity():
    repo = SQLiteOpportunityRepository(sqlite3.connect(":memory:"))
    item = make_opportunity()
    repo.save(item)
    item.name = "Updated"
    item.probability = Decimal("80")
    repo.save(item)
    loaded = repo.get(item.tenant_id, item.id)
    assert loaded.name == "Updated"
    assert loaded.probability == Decimal("80")


def test_delete_is_tenant_scoped():
    repo = SQLiteOpportunityRepository(sqlite3.connect(":memory:"))
    item = make_opportunity()
    repo.save(item)
    repo.delete("tenant-2", item.id)
    assert repo.get("tenant-1", item.id) is not None
    repo.delete("tenant-1", item.id)
    assert repo.get("tenant-1", item.id) is None
