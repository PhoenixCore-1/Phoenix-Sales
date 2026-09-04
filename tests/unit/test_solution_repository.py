from uuid import uuid4

from phoenix_sales.domain.solution import Solution, SolutionComponent, SolutionComponentType
from phoenix_sales.persistence.in_memory_solution_repository import InMemorySolutionRepository


def solution(tenant="tenant-1", opportunity_id=None, name="Solution"):
    return Solution(
        tenant_id=tenant,
        opportunity_id=opportunity_id or uuid4(),
        name=name,
        requirement="Requirement",
        application="Application",
    )


def test_save_and_get_are_tenant_scoped():
    repo = InMemorySolutionRepository()
    item = solution()
    repo.save(item)
    assert repo.get("tenant-1", item.id) is item
    assert repo.get("tenant-2", item.id) is None


def test_list_by_opportunity_is_tenant_scoped():
    repo = InMemorySolutionRepository()
    opportunity = uuid4()
    first = solution("tenant-1", opportunity, "First")
    second = solution("tenant-1", opportunity, "Second")
    other = solution("tenant-2", opportunity, "Other")
    repo.save(first)
    repo.save(second)
    repo.save(other)
    results = repo.list_by_opportunity("tenant-1", opportunity)
    assert results == [first, second]


def test_list_by_opportunity_excludes_other_opportunities():
    repo = InMemorySolutionRepository()
    target = uuid4()
    first = solution(opportunity_id=target)
    other = solution(opportunity_id=uuid4())
    repo.save(first)
    repo.save(other)
    assert repo.list_by_opportunity("tenant-1", target) == [first]


def test_save_replaces_same_solution_identity():
    repo = InMemorySolutionRepository()
    item = solution()
    repo.save(item)
    item.name = "Updated"
    repo.save(item)
    assert repo.get("tenant-1", item.id).name == "Updated"


def test_delete_is_tenant_scoped_and_idempotent():
    repo = InMemorySolutionRepository()
    item = solution()
    repo.save(item)
    repo.delete("tenant-2", item.id)
    assert repo.get("tenant-1", item.id) is item
    repo.delete("tenant-1", item.id)
    assert repo.get("tenant-1", item.id) is None
    repo.delete("tenant-1", item.id)


def test_solution_components_are_retained():
    repo = InMemorySolutionRepository()
    item = solution()
    item.add_component(SolutionComponent(SolutionComponentType.PRODUCT, "P-1", "Product", 2, is_recommended=True))
    repo.save(item)
    loaded = repo.get("tenant-1", item.id)
    assert loaded.components[0].item_id == "P-1"
    assert loaded.components[0].is_recommended is True
