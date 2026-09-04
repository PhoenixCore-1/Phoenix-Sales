"""Application service for persistent Sales opportunities."""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from phoenix_sales.api.contracts import RequestContext
from phoenix_sales.domain.opportunity import Opportunity, OpportunityStage
from phoenix_sales.domain.opportunity_lifecycle import validate_transition
from phoenix_sales.persistence.in_memory_opportunity_repository import InMemoryOpportunityRepository
from phoenix_sales.persistence.opportunity_repository import OpportunityRepository


@dataclass(frozen=True)
class OpportunityOutcome:
    """Controlled outcome information for terminal opportunity states."""

    reason: str
    deferred_until: date | None = None


class OpportunityService:
    """Coordinate opportunity commands, queries, and persistence."""

    CREATE_PERMISSION = "sales.opportunity.create"
    READ_PERMISSION = "sales.opportunity.read"
    UPDATE_PERMISSION = "sales.opportunity.update"
    TRANSITION_PERMISSION = "sales.opportunity.transition"

    def __init__(self, context: RequestContext, repository: OpportunityRepository | None = None) -> None:
        self._context = context
        self._repository = repository or InMemoryOpportunityRepository()

    def create_opportunity(self, *, name: str, customer_id: str, owner_user_id: str,
                           contact_id: str | None = None, requirement: str | None = None,
                           application: str | None = None, estimated_value: Decimal | None = None,
                           close_date: date | None = None, source: str | None = None,
                           project_id: str | None = None) -> Opportunity:
        self._require(self.CREATE_PERMISSION)
        opportunity = Opportunity(
            tenant_id=self._context.tenant.tenant_id, name=name, customer_id=customer_id,
            owner_user_id=owner_user_id, contact_id=contact_id, requirement=requirement,
            application=application, estimated_value=estimated_value, close_date=close_date,
            source=source, project_id=project_id,
        )
        return self._repository.save(opportunity)

    def get_opportunity(self, opportunity_id: UUID) -> Opportunity | None:
        self._require(self.READ_PERMISSION)
        return self._repository.get(self._context.tenant.tenant_id, opportunity_id)

    def list_by_customer(self, customer_id: str) -> list[Opportunity]:
        self._require(self.READ_PERMISSION)
        return self._repository.list_by_customer(self._context.tenant.tenant_id, customer_id)

    def list_by_owner(self, owner_user_id: str) -> list[Opportunity]:
        self._require(self.READ_PERMISSION)
        return self._repository.list_by_owner(self._context.tenant.tenant_id, owner_user_id)

    def update_opportunity(self, opportunity: Opportunity, **changes: object) -> Opportunity:
        self._require(self.UPDATE_PERMISSION)
        self._require_tenant(opportunity)
        if opportunity.is_terminal:
            raise ValueError("terminal opportunity cannot be updated")
        protected = {"id", "tenant_id", "created_at", "updated_at", "stage"}
        forbidden = protected.intersection(changes)
        if forbidden:
            raise ValueError(f"protected opportunity fields cannot be updated: {', '.join(sorted(forbidden))}")
        for field_name, value in changes.items():
            if not hasattr(opportunity, field_name):
                raise ValueError(f"unknown opportunity field: {field_name}")
            setattr(opportunity, field_name, value)
        opportunity.updated_at = datetime.now(timezone.utc)
        return self._repository.save(opportunity)

    def transition_opportunity(self, opportunity: Opportunity, target: OpportunityStage,
                               *, outcome: OpportunityOutcome | None = None) -> Opportunity:
        self._require(self.TRANSITION_PERMISSION)
        self._require_tenant(opportunity)
        validate_transition(opportunity.stage, target)
        self._validate_transition_requirements(opportunity, target, outcome)
        opportunity.transition_to(target)
        if outcome is not None:
            opportunity.outcome_reason = outcome.reason
            opportunity.deferred_until = outcome.deferred_until
            if target is OpportunityStage.LOST:
                opportunity.lost_reason = outcome.reason
        return self._repository.save(opportunity)

    def set_probability(self, opportunity: Opportunity, probability: Decimal) -> Opportunity:
        self._require(self.UPDATE_PERMISSION)
        self._require_tenant(opportunity)
        if opportunity.is_terminal:
            raise ValueError("terminal opportunity cannot be updated")
        opportunity.set_probability(probability)
        return self._repository.save(opportunity)

    def _validate_transition_requirements(self, opportunity, target, outcome) -> None:
        if target in {OpportunityStage.QUALIFIED, OpportunityStage.DISCOVERY,
                      OpportunityStage.SOLUTION_DEVELOPMENT, OpportunityStage.QUOTE,
                      OpportunityStage.NEGOTIATION} and not (opportunity.requirement and opportunity.requirement.strip()):
            raise ValueError(f"{target.value} requires requirement")
        if target in {OpportunityStage.DISCOVERY, OpportunityStage.SOLUTION_DEVELOPMENT,
                      OpportunityStage.QUOTE, OpportunityStage.NEGOTIATION} and not (opportunity.application and opportunity.application.strip()):
            raise ValueError(f"{target.value} requires application")
        if target in {OpportunityStage.QUOTE, OpportunityStage.NEGOTIATION}:
            if opportunity.estimated_value is None:
                raise ValueError(f"{target.value} requires estimated_value")
            if opportunity.close_date is None:
                raise ValueError(f"{target.value} requires close_date")
        if target in {OpportunityStage.LOST, OpportunityStage.NO_DECISION,
                      OpportunityStage.CANCELLED, OpportunityStage.NURTURE,
                      OpportunityStage.DEFERRED}:
            if outcome is None or not outcome.reason.strip():
                raise ValueError(f"{target.value} requires an outcome reason")
        if target is OpportunityStage.DEFERRED and outcome is None or target is OpportunityStage.DEFERRED and outcome.deferred_until is None:
            raise ValueError("DEFERRED requires deferred_until")

    def _require(self, permission: str) -> None:
        if not self._context.has_permission(permission):
            raise PermissionError(f"missing permission: {permission}")

    def _require_tenant(self, opportunity: Opportunity) -> None:
        if opportunity.tenant_id != self._context.tenant.tenant_id:
            raise PermissionError("opportunity belongs to another tenant")
