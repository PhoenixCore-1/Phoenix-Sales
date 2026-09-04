from phoenix_sales.domain.opportunity import Opportunity
from phoenix_sales.persistence.in_memory_opportunity_repository import InMemoryOpportunityRepository


def make_opportunity(tenant: str = "tenant-1", customer: str = "customer-1", owner: str = "user-1") -> Opportunity:
    return Opportunity(
        tenant_id=tenant,
        name="Test opportunity",
        customer_id=customer,
        owner_user_id=owner,
    )


def test_save_and_get_are_tenant_scoped():
    repo = InMemoryOpportunityRepository()
    item = make_opportunity()
    repo.save(item)
    assert repo.get("tenant-1", item.id) is item
    assert repo.get("tenant-2", item.id) is None


def test_list_by_customer_is_tenant_scoped():
    repo = InMemoryOpportunityRepository()
    first = make_opportunity(customer="customer-1")
    second = make_opportunity(customer="customer-2")
    other_tenant = make_opportunity(tenant="tenant-2", customer="customer-1")
    for item in (first, second, other_tenant):
        repo.save(item)
    assert repo.list_by_customer("tenant-1", "customer-1") == [first]


def test_list_by_owner_is_tenant_scoped():
    repo = InMemoryOpportunityRepository()
    first = make_opportunity(owner="user-1")
    second = make_opportunity(owner="user-2")
    other_tenant = make_opportunity(tenant="tenant-2", owner="user-1")
    for item in (first, second, other_tenant):
        repo.save(item)
    assert repo.list_by_owner("tenant-1", "user-1") == [first]


def test_save_replaces_same_tenant_identity():
    repo = InMemoryOpportunityRepository()
    item = make_opportunity()
    repo.save(item)
    item.name = "Updated"
    repo.save(item)
    assert repo.get("tenant-1", item.id).name == "Updated"


def test_delete_is_tenant_scoped_and_idempotent():
    repo = InMemoryOpportunityRepository()
    item = make_opportunity()
    repo.save(item)
    repo.delete("tenant-2", item.id)
    assert repo.get("tenant-1", item.id) is item
    repo.delete("tenant-1", item.id)
    repo.delete("tenant-1", item.id)
    assert repo.get("tenant-1", item.id) is None
