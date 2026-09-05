"""Application commands and queries for competitor pricing intelligence."""
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from phoenix_sales.domain.competitor_pricing import CompetitorPriceObservation
from phoenix_sales.services.competitor_pricing import CompetitorPricingService


@dataclass(frozen=True)
class CreateCompetitorPricingCommand:
    observation: CompetitorPriceObservation

@dataclass(frozen=True)
class GetCompetitorPricingQuery:
    observation_id: UUID

@dataclass(frozen=True)
class ListCompetitorPricingQuery:
    competitor: str | None = None
    comparable_product_id: str | None = None
    customer_id: str | None = None
    project_id: str | None = None
    observed_from: date | None = None
    observed_to: date | None = None

@dataclass(frozen=True)
class UpdateCompetitorPricingCommand:
    observation_id: UUID
    changes: dict[str, object]


class CompetitorPricingApplication:
    def __init__(self, service: CompetitorPricingService) -> None:
        self.service = service

    def create(self, command: CreateCompetitorPricingCommand) -> CompetitorPriceObservation:
        return self.service.create(command.observation)

    def get(self, query: GetCompetitorPricingQuery) -> CompetitorPriceObservation:
        return self.service.get(query.observation_id)

    def list(self, query: ListCompetitorPricingQuery) -> list[CompetitorPriceObservation]:
        return self.service.list(competitor=query.competitor, comparable_product_id=query.comparable_product_id, customer_id=query.customer_id, project_id=query.project_id, observed_from=query.observed_from, observed_to=query.observed_to)

    def update(self, command: UpdateCompetitorPricingCommand) -> CompetitorPriceObservation:
        return self.service.update(command.observation_id, **command.changes)
