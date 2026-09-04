"""Application service for Phoenix Sales Solutions."""

from phoenix_sales.api.contracts import RequestContext
from phoenix_sales.domain.solution import Solution, SolutionComponent, SolutionStatus
from phoenix_sales.domain.solution_lifecycle import validate_transition
from phoenix_sales.persistence.solution_repository import SolutionRepository


class SolutionService:
    """Coordinate Solution commands, persistence, permissions, and lifecycle."""

    CREATE_PERMISSION = "sales.solution.create"
    READ_PERMISSION = "sales.solution.read"
    UPDATE_PERMISSION = "sales.solution.update"
    REVIEW_PERMISSION = "sales.solution.review"
    APPROVE_PERMISSION = "sales.solution.approve"
    CANCEL_PERMISSION = "sales.solution.cancel"
    SUPERSEDE_PERMISSION = "sales.solution.supersede"

    def __init__(self, context: RequestContext, repository: SolutionRepository) -> None:
        self._context = context
        self._repository = repository

    def create_solution(self, *, opportunity_id, name: str, requirement: str,
                        application: str, project_id: str | None = None,
                        site_id: str | None = None) -> Solution:
        self._require(self.CREATE_PERMISSION)
        solution = Solution(
            tenant_id=self._context.tenant.tenant_id,
            opportunity_id=opportunity_id,
            name=name,
            requirement=requirement,
            application=application,
            project_id=project_id,
            site_id=site_id,
        )
        return self._repository.save(solution)

    def get_solution(self, solution_id) -> Solution | None:
        self._require(self.READ_PERMISSION)
        return self._repository.get(self._context.tenant.tenant_id, solution_id)

    def list_by_opportunity(self, opportunity_id):
        self._require(self.READ_PERMISSION)
        return self._repository.list_by_opportunity(self._context.tenant.tenant_id, opportunity_id)

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
        return self._repository.save(solution)

    def add_component(self, solution: Solution, component: SolutionComponent) -> Solution:
        self._require(self.UPDATE_PERMISSION)
        self._require_tenant(solution)
        self._ensure_editable(solution)
        solution.add_component(component)
        return self._repository.save(solution)

    def submit_for_review(self, solution: Solution) -> Solution:
        self._require(self.REVIEW_PERMISSION)
        self._require_tenant(solution)
        validate_transition(solution.status, SolutionStatus.IN_REVIEW)
        solution.submit_for_review()
        return self._repository.save(solution)

    def approve(self, solution: Solution) -> Solution:
        self._require(self.APPROVE_PERMISSION)
        self._require_tenant(solution)
        validate_transition(solution.status, SolutionStatus.APPROVED)
        self._validate_content(solution)
        solution.approve()
        return self._repository.save(solution)

    def cancel(self, solution: Solution) -> Solution:
        self._require(self.CANCEL_PERMISSION)
        self._require_tenant(solution)
        validate_transition(solution.status, SolutionStatus.CANCELLED)
        solution.cancel()
        return self._repository.save(solution)

    def supersede(self, solution: Solution) -> Solution:
        self._require(self.SUPERSEDE_PERMISSION)
        self._require_tenant(solution)
        validate_transition(solution.status, SolutionStatus.SUPERSEDED)
        solution.status = SolutionStatus.SUPERSEDED
        return self._repository.save(solution)

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
