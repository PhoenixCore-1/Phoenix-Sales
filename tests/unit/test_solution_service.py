from uuid import uuid4

import pytest

from phoenix_sales.api.contracts import PermissionContext, RequestContext, TenantContext, UserContext
from phoenix_sales.domain.solution import SolutionComponent, SolutionComponentType, SolutionStatus
from phoenix_sales.services.solution import SolutionService

TENANT = "tenant-1"


def context(*permissions: str) -> RequestContext:
    return RequestContext(
        tenant=TenantContext(TENANT),
        user=UserContext("user-1"),
        permissions=PermissionContext(frozenset(permissions)),
    )


def service(*permissions: str) -> SolutionService:
    return SolutionService(context(*permissions))


def component(recommended=False):
    return SolutionComponent(
        SolutionComponentType.PRODUCT, "item-1", "Primary component", 2,
        is_recommended=recommended,
    )


def make_solution():
    return service("sales.solution.create").create_solution(
        opportunity_id=uuid4(), name="Solution", requirement="Requirement", application="Application"
    )


def test_create_requires_permission_and_uses_tenant():
    solution = make_solution()
    assert solution.tenant_id == TENANT
    with pytest.raises(PermissionError, match="sales.solution.create"):
        service().create_solution(opportunity_id=uuid4(), name="S", requirement="R", application="A")


def test_read_requires_permission_and_tenant():
    solution = make_solution()
    assert service("sales.solution.read").get_solution(solution) is solution
    other = SolutionService(
        RequestContext(TenantContext("tenant-2"), UserContext("user-1"), PermissionContext(frozenset({"sales.solution.read"})))
    )
    with pytest.raises(PermissionError, match="another tenant"):
        other.get_solution(solution)


def test_update_rejects_protected_fields():
    solution = make_solution()
    with pytest.raises(ValueError, match="protected"):
        service("sales.solution.update").update_solution(solution, version=2)


def test_update_rejects_unknown_fields():
    solution = make_solution()
    with pytest.raises(ValueError, match="unknown"):
        service("sales.solution.update").update_solution(solution, unknown="x")


def test_add_component_requires_update_permission():
    solution = make_solution()
    with pytest.raises(PermissionError, match="sales.solution.update"):
        service().add_component(solution, component())
    service("sales.solution.update").add_component(solution, component())
    assert len(solution.components) == 1


def test_submit_requires_review_permission_and_component():
    solution = make_solution()
    with pytest.raises(PermissionError, match="sales.solution.review"):
        service().submit_for_review(solution)
    with pytest.raises(ValueError, match="at least one component"):
        service("sales.solution.review").submit_for_review(solution)


def test_approval_requires_recommended_component():
    solution = make_solution()
    svc = service("sales.solution.update", "sales.solution.review", "sales.solution.approve")
    svc.add_component(solution, component(False))
    svc.submit_for_review(solution)
    with pytest.raises(ValueError, match="recommended component"):
        svc.approve(solution)


def test_approve_and_lock_solution():
    solution = make_solution()
    svc = service("sales.solution.update", "sales.solution.review", "sales.solution.approve")
    svc.add_component(solution, component(True))
    svc.submit_for_review(solution)
    svc.approve(solution)
    assert solution.status is SolutionStatus.APPROVED
    with pytest.raises(ValueError, match="locked"):
        svc.add_component(solution, component(True))


def test_cancel_requires_permission_and_closes_solution():
    solution = make_solution()
    with pytest.raises(PermissionError, match="sales.solution.cancel"):
        service().cancel(solution)
    service("sales.solution.cancel").cancel(solution)
    assert solution.status is SolutionStatus.CANCELLED


def test_supersede_requires_approval_and_permission():
    solution = make_solution()
    svc = service("sales.solution.update", "sales.solution.review", "sales.solution.approve", "sales.solution.supersede")
    svc.add_component(solution, component(True))
    svc.submit_for_review(solution)
    svc.approve(solution)
    svc.supersede(solution)
    assert solution.status is SolutionStatus.SUPERSEDED


def test_cross_tenant_update_is_denied():
    solution = make_solution()
    other = SolutionService(
        RequestContext(TenantContext("tenant-2"), UserContext("user-1"), PermissionContext(frozenset({"sales.solution.update"})))
    )
    with pytest.raises(PermissionError, match="another tenant"):
        other.update_solution(solution, name="No")
