import sqlite3
from uuid import uuid4

from phoenix_sales.domain.solution import Solution, SolutionComponent, SolutionComponentType, SolutionStatus
from phoenix_sales.persistence.sqlite_solution_repository import SQLiteSolutionRepository


def make_solution(tenant="tenant-1", opportunity_id=None):
    solution = Solution(
        tenant_id=tenant,
        opportunity_id=opportunity_id or uuid4(),
        name="Anchoring Solution",
        requirement="Secure the structure",
        application="Concrete substrate",
        version=2,
        project_id="project-1",
        site_id="site-1",
        technical_parameters={"embedment": "80mm", "substrate": "C25/30"},
        constraints=["Edge distance"],
        compliance_requirements=["Specification X"],
        technical_rationale="Selected for the application.",
        commercial_rationale="Best balanced option.",
        status=SolutionStatus.IN_REVIEW,
    )
    solution.add_component(SolutionComponent(
        SolutionComponentType.PRODUCT, "P-100", "Primary anchor", 10,
        unit="EA", alternative_group="A", is_recommended=True,
    ))
    solution.add_component(SolutionComponent(
        SolutionComponentType.ACCESSORY, "A-100", "Accessory", 10,
        unit="EA", alternative_group="A",
    ))
    return solution


def repo():
    connection = sqlite3.connect(":memory:")
    return SQLiteSolutionRepository(connection)


def test_round_trip_preserves_solution_and_components():
    repository = repo()
    original = make_solution()
    repository.save(original)
    loaded = repository.get("tenant-1", original.id)
    assert loaded is not None
    assert loaded.id == original.id
    assert loaded.opportunity_id == original.opportunity_id
    assert loaded.version == 2
    assert loaded.technical_parameters == original.technical_parameters
    assert loaded.constraints == original.constraints
    assert loaded.compliance_requirements == original.compliance_requirements
    assert loaded.status is SolutionStatus.IN_REVIEW
    assert loaded.components == original.components


def test_get_is_tenant_scoped():
    repository = repo()
    original = make_solution()
    repository.save(original)
    assert repository.get("tenant-2", original.id) is None


def test_list_by_opportunity_is_tenant_scoped_and_ordered():
    repository = repo()
    opportunity = uuid4()
    first = make_solution(opportunity_id=opportunity)
    second = make_solution(opportunity_id=opportunity)
    second.version = 3
    other = make_solution("tenant-2", opportunity)
    repository.save(second)
    repository.save(first)
    repository.save(other)
    assert repository.list_by_opportunity("tenant-1", opportunity) == [first, second]


def test_save_updates_solution_and_replaces_components():
    repository = repo()
    original = make_solution()
    repository.save(original)
    original.name = "Updated Solution"
    original.components.clear()
    original.add_component(SolutionComponent(
        SolutionComponentType.SERVICE, "S-1", "Installation", 1,
        unit="JOB", is_recommended=True,
    ))
    repository.save(original)
    loaded = repository.get("tenant-1", original.id)
    assert loaded.name == "Updated Solution"
    assert len(loaded.components) == 1
    assert loaded.components[0].component_type is SolutionComponentType.SERVICE


def test_delete_is_tenant_scoped_and_idempotent():
    repository = repo()
    original = make_solution()
    repository.save(original)
    repository.delete("tenant-2", original.id)
    assert repository.get("tenant-1", original.id) is not None
    repository.delete("tenant-1", original.id)
    assert repository.get("tenant-1", original.id) is None
    repository.delete("tenant-1", original.id)
