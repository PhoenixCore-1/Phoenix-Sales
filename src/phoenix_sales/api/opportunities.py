"""Application command/query boundary for Phoenix Sales opportunities.

The platform-facing API accepts simple request objects and delegates all
business rules and persistence to the OpportunityService. Callers do not need
to know the repository or database implementation.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from phoenix_sales.domain.opportunity import Opportunity, OpportunityStage
from phoenix_sales.services.opportunity import OpportunityOutcome, OpportunityService


@dataclass(frozen=True)
class CreateOpportunityCommand:
    name: str
    customer_id: str
    owner_user_id: str
    contact_id: str | None = None
    requirement: str | None = None
    application: str | None = None
    estimated_value: Decimal | None = None
    close_date: date | None = None
    source: str | None = None
    project_id: str | None = None


@dataclass(frozen=True)
class UpdateOpportunityCommand:
    opportunity: Opportunity
    changes: dict[str, object]


@dataclass(frozen=True)
class TransitionOpportunityCommand:
    opportunity: Opportunity
    target: OpportunityStage
    outcome: OpportunityOutcome | None = None


@dataclass(frozen=True)
class SetOpportunityProbabilityCommand:
    opportunity: Opportunity
    probability: Decimal


@dataclass(frozen=True)
class GetOpportunityQuery:
    opportunity_id: UUID


@dataclass(frozen=True)
class ListCustomerOpportunitiesQuery:
    customer_id: str


@dataclass(frozen=True)
class ListOwnerOpportunitiesQuery:
    owner_user_id: str


class OpportunityApplication:
    """Controlled application boundary for Opportunity commands and queries."""

    def __init__(self, service: OpportunityService) -> None:
        self._service = service

    def create(self, command: CreateOpportunityCommand) -> Opportunity:
        return self._service.create_opportunity(
            name=command.name,
            customer_id=command.customer_id,
            owner_user_id=command.owner_user_id,
            contact_id=command.contact_id,
            requirement=command.requirement,
            application=command.application,
            estimated_value=command.estimated_value,
            close_date=command.close_date,
            source=command.source,
            project_id=command.project_id,
        )

    def get(self, query: GetOpportunityQuery) -> Opportunity | None:
        return self._service.get_opportunity(query.opportunity_id)

    def update(self, command: UpdateOpportunityCommand) -> Opportunity:
        return self._service.update_opportunity(command.opportunity, **command.changes)

    def transition(self, command: TransitionOpportunityCommand) -> Opportunity:
        return self._service.transition_opportunity(
            command.opportunity,
            command.target,
            outcome=command.outcome,
        )

    def set_probability(self, command: SetOpportunityProbabilityCommand) -> Opportunity:
        return self._service.set_probability(command.opportunity, command.probability)

    def list_by_customer(self, query: ListCustomerOpportunitiesQuery) -> list[Opportunity]:
        return self._service.list_by_customer(query.customer_id)

    def list_by_owner(self, query: ListOwnerOpportunitiesQuery) -> list[Opportunity]:
        return self._service.list_by_owner(query.owner_user_id)
