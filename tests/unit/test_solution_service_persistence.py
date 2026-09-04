import sqlite3
from uuid import uuid4

import pytest

from phoenix_sales.api.contracts import PermissionContext, RequestContext, TenantContext, UserContext
from phoenix_sales.domain.solution import SolutionComponent, SolutionComponentType, SolutionStatus
from phoenix_sales.persistence.sqlite_solution_repository import SQLiteSolutionRepository
from phoenix_sales.services.solution import SolutionService


def context(*permissions: str) -> RequestContext:
    return RequestContext(
        TenantContext("tenant-1"), UserContext("user-1"), PermissionContext(frozenset(permissions))
    )


def make_service(*permissions: str) -> SolutionService:
    return SolutionService(context(*permissions), SQLiteSolutionRepository(sqlite3.connect(":memory:")))


def component():
    return SolutionComponent(SolutionComponentType.PRODUCT, "P-1", "Primary", 1, is_recommended=True)


def test_create_persists_solution():
    repository = SQLiteSolutionRepository(sqlite3.connect(":memory:"))
    service = SolutionService(context("sales.solution.create", "sales.solution.read"), repository)
    created = service.create_solution(opportunity_id=uuid4(), name="S", requirement="R", application="A")
    assert repository.get("tenant-1", created.id) is not None


def test_get_reads_through_repository():
    repository = SQLiteSolutionRepository(sqlite3.connect(":memory:"))
    service = SolutionService(context("sales.solution.create", "sales.solution.read"), repository)
    created = service.create_solution(opportunity_id=uuid4(), name="S", requirement="R", application="A")
    loaded = service.get_solution(created.id)
    assert loaded is not None
    assert loaded.id == created.id


def test_list_by_opportunity_reads_persisted_solutions():
    repository = SQLiteSolutionRepository(sqlite3.connect(":memory:"))
    service = SolutionService(context("sales.solution.create", "sales.solution.read"), repository)
    opportunity = uuid4()
    created = service.create_solution(opportunity_id=opportunity, name="S", requirement="R", application="A")
    assert service.list_by_opportunity(opportunity) == [created]


def test_commands_persist_state_changes():
    repository = SQLiteSolutionRepository(sqlite3.connect(":memory:"))
    service = SolutionService(
        context("sales.solution.create", "sales.solution.read", "sales.solution.update", "sales.solution.review", "sales.solution.approve"),
        repository,
    )
    created = service.create_solution(opportunity_id=uuid4(), name="S", requirement="R", application="A")
    service.add_component(created, component())
    service.submit_for_review(created)
    service.approve(created)
    loaded = service.get_solution(created.id)
    assert loaded.status is SolutionStatus.APPROVED
    assert len(loaded.components) == 1


def test_service_never_reads_another_tenant():
    repository = SQLiteSolutionRepository(sqlite3.connect(":memory:"))
    creator = SolutionService(context("sales.solution.create"), repository)
    created = creator.create_solution(opportunity_id=uuid4(), name="S", requirement="R", application="A")
    other_context = RequestContext(TenantContext("tenant-2"), UserContext("user-2"), PermissionContext(frozenset({"sales.solution.read"})))
    other = SolutionService(other_context, repository)
    assert other.get_solution(created.id) is None


def test_missing_repository_is_not_allowed():
    with pytest.raises(TypeError):
        SolutionService(context("sales.solution.create"))
