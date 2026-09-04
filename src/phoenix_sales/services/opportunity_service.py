"""Application service boundary for Phoenix Sales opportunities."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from phoenix_sales.api.contracts import RequestContext
from phoenix_sales.domain.opportunity import Opportunity, OpportunityStage
from phoenix_sales.domain.opportunity_lifecycle import validate_transition


@dataclass(frozen=True)
class OpportunityOutcome:
    """Controlled outcome information for terminal opportunity states."""

    reason: str
    deferred_until: date | None = None


class OpportunityService:
    """Coordinate opportunity commands without exposing persistence details."""

    CREATE_PERMISSION = "sales.opportunity.create"
    UPDATE_PERMISSION = "sales.opportunity.update"
    TRANSITION_PERMISSION = "sales.opportunity.transition"

    def __init__(self, context: RequestContext) -> None:
        self._context = context

    def create_opportunity(
        self,
        *,
        name: str,
        customer_id: str,
        owner_user_id: str,
        contact_id: str | None = None,
        requirement: str | None = None,
        application: str | None = None,
        estimated_value: Decimal | None = None,
        close_date: date | None = None,
        source: str | None = None,
        project_id: str | None = None,
    ) -> Opportunity:
        self._require(self.CREATE_PERMISSION)
        return Opportunity(
            tenant_id=self._context.tenant.tenant_id,
            name=name,
            customer_id=customer_id,
            owner_user_id=owner_user_id,
            contact_id=contact_id,
            requirement=requirement,
            application=application,
            estimated_value=estimated_value,
            close_date=close_date,
            source=source,
            project_id=project_id,
        )

    def update_opportunity(self, opportunity: Opportunity, **changes: object) -> Opportunity:
        self._require(self.UPDATE_PERMISSION)
        self._require_tenant(opportunity)

        if opportunity.is_terminal:
            raise ValueError("terminal opportunity cannot be updated")

        protected = {"id", "tenant_id", "created_at", "updated_at", "stage"}
        forbidden = protected.intersection(changes)
        if forbidden:
            fields = ", ".join(sorted(forbidden))
            raise ValueError(f"protected opportunity fields cannot be updated: {fields}")

        for field_name, value in changes.items():
            if not hasattr(opportunity, field_name):
                raise ValueError(f"unknown opportunity field: {field_name}")
            setattr(opportunity, field_name, value)

        self._validate_stage_requirements(opportunity, opportunity.stage)
        return opportunity

    def transition_opportunity(
        self,
        opportunity: Opportunity,
        target: OpportunityStage,
        *,
        outcome: OpportunityOutcome | None = None,
    ) -> Opportunity:
        self._require(self.TRANSITION_PERMISSION)
        self._require_tenant(opportunity)
        validate_transition(opportunity.stage, target)
        self._validate_transition_requirements(opportunity, target, outcome)
        opportunity.transition_to(target)
        return opportunity

    def set_probability(self, opportunity: Opportunity, probability: Decimal) -> Opportunity:
        self._require(self.UPDATE_PERMISSION)
        self._require_tenant(opportunity)
        if opportunity.is_terminal:
            raise ValueError("terminal opportunity cannot be updated")
        opportunity.set_probability(probability)
        return opportunity

    def _validate_transition_requirements(
        self,
        opportunity: Opportunity,
        target: OpportunityStage,
        outcome: OpportunityOutcome | None,
    ) -> None:
        self._validate_stage_requirements(opportunity, target)

        if target in {
            OpportunityStage.LOST,
            OpportunityStage.NO_DECISION,
            OpportunityStage.CANCELLED,
            OpportunityStage.NURTURE,
            OpportunityStage.DEFERRED,
        }:
            if outcome is None or not outcome.reason.strip():
                raise ValueError(f"{target.value} requires an outcome reason")

        if target == OpportunityStage.DEFERRED and outcome and outcome.deferred_until is None:
            raise ValueError("DEFERRED requires deferred_until")

    @staticmethod
    def _validate_stage_requirements(opportunity: Opportunity, stage: OpportunityStage) -> None:
        if stage in {
            OpportunityStage.QUALIFIED,
            OpportunityStage.DISCOVERY,
            OpportunityStage.SOLUTION_DEVELOPMENT,
            OpportunityStage.QUOTE,
            OpportunityStage.NEGOTIATION,
        } and not (opportunity.requirement and opportunity.requirement.strip()):
            raise ValueError(f"{stage.value} requires requirement")

        if stage in {
            OpportunityStage.DISCOVERY,
            OpportunityStage.SOLUTION_DEVELOPMENT,
            OpportunityStage.QUOTE,
            OpportunityStage.NEGOTIATION,
        } and not (opportunity.application and opportunity.application.strip()):
            raise ValueError(f"{stage.value} requires application")

        if stage in {OpportunityStage.QUOTE, OpportunityStage.NEGOTIATION}:
            if opportunity.estimated_value is None:
                raise ValueError(f"{stage.value} requires estimated_value")
            if opportunity.close_date is None:
                raise ValueError(f"{stage.value} requires close_date")

    def _require(self, permission: str) -> None:
        if not self._context.has_permission(permission):
            raise PermissionError(f"missing permission: {permission}")

    def _require_tenant(self, opportunity: Opportunity) -> None:
        if opportunity.tenant_id != self._context.tenant.tenant_id:
            raise PermissionError("opportunity belongs to another tenant")
