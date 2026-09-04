"""Application service for Phoenix Sales Solutions."""

from phoenix_sales.api.contracts import RequestContext
from phoenix_sales.domain.solution import Solution, SolutionComponent, SolutionStatus
from phoenix_sales.domain.solution_lifecycle import validate_transition


class SolutionService:
    """Coordinate Solution commands while enforcing tenant and permissions."""

    CREATE_PERMISSION = "sales.solution.create"
    READ_PERMISSION = "sales.solution.read"
    UPDATE_PERMISSION = "sales.solution.update"
    REVIEW_PERMISSION = "sales.solution.review"
    APPROVE_PERMISSION = "sales.solution.approve"
    CANCEL_PERMISSION = "sales.solution.cancel"
    SUPERSEDE_PERMISSION = "sales.solution.supersede"

    def __init__(self, context: RequestContext) -> None:
        self._context = context

    def create_solution(self, *, opportunity_id, name: str, requirement: str,
                        application: str, project_id: str | None = None,
                        site_id: str | None = None) -> Solution:
        self._require(self.CREATE_PERMISSION)
        return Solution(
            tenant_id=self._context.tenant.tenant_id,
            opportunity_id=opportunity_id,
            name=name,
            requirement=requirement,
            application=application,
            project_id=project_id,
            site_id=site_id,
        )

    def get_solution(self, solution: Solution) -> Solution:
        self._require(self.READ_PERMISSION)
        self._require_tenant(solution)
        return solution

    def update_solution(self, solution: Solution, **changes: object) -> Solution:
        self._require(self.UPDATE_PERMISSION)
        self._require_tenant(solution)
        self._ensure_editable(solution)
        protected = {"id", "tenant_id", "opportunity_id", "version", "status", "created_at", "updated_at"}
        forbidden = protected.intersection(changes)
        if forbidden:
            raise ValueError(f"protected solution fields cannot be updated: {', '.join(sorted(forbidden))}")
        for field_name, value in changes.items():
            if not hasattr(solution, field_name):
                raise ValueError(f"unknown solution field: {field_name}")
            setattr(solution, field_name, value)
        self._validate_content(solution)
        return solution

    def add_component(self, solution: Solution, component: SolutionComponent) -> Solution:
        self._require(self.UPDATE_PERMISSION)
        self._require_tenant(solution)
        self._ensure_editable(solution)
        solution.add_component(component)
        return solution

    def submit_for_review(self, solution: Solution) -> Solution:
        self._require(self.REVIEW_PERMISSION)
        self._require_tenant(solution)
        validate_transition(solution.status, SolutionStatus.IN_REVIEW)
        solution.submit_for_review()
        return solution

    def approve(self, solution: Solution) -> Solution:
        self._require(self.APPROVE_PERMISSION)
        self._require_tenant(solution)
        validate_transition(solution.status, SolutionStatus.APPROVED)
        self._validate_content(solution)
        solution.approve()
        return solution

    def cancel(self, solution: Solution) -> Solution:
        self._require(self.CANCEL_PERMISSION)
        self._require_tenant(solution)
        validate_transition(solution.status, SolutionStatus.CANCELLED)
        solution.cancel()
        return solution

    def supersede(self, solution: Solution) -> Solution:
        self._require(self.SUPERSEDE_PERMISSION)
        self._require_tenant(solution)
        validate_transition(solution.status, SolutionStatus.SUPERSEDED)
        solution.status = SolutionStatus.SUPERSEDED
        return solution

    @staticmethod
    def _validate_content(solution: Solution) -> None:
        if not solution.components:
            raise ValueError("solution requires at least one component")
        if not any(component.is_recommended for component in solution.components):
            raise ValueError("solution requires a recommended component")

    def _ensure_editable(self, solution: Solution) -> None:
        if solution.is_locked:
            raise ValueError("locked solution cannot be changed")

    def _require(self, permission: str) -> None:
        if not self._context.has_permission(permission):
            raise PermissionError(f"missing permission: {permission}")

    def _require_tenant(self, solution: Solution) -> None:
        if solution.tenant_id != self._context.tenant.tenant_id:
            raise PermissionError("solution belongs to another tenant")
