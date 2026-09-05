"""Application boundary contracts for pipeline and forecasting."""
from dataclasses import dataclass
from uuid import UUID

from phoenix_sales.domain.pipeline_forecast import PipelineSnapshot, SalesForecast
from phoenix_sales.services.pipeline_forecast import PipelineForecastService


@dataclass(frozen=True)
class RecordPipelineSnapshotCommand:
    snapshot: PipelineSnapshot


@dataclass(frozen=True)
class GetPipelineSnapshotsQuery:
    opportunity_id: UUID


@dataclass(frozen=True)
class CreateForecastCommand:
    forecast: SalesForecast


@dataclass(frozen=True)
class GetForecastQuery:
    forecast_id: UUID


@dataclass(frozen=True)
class ListForecastsQuery:
    scope_id: str


@dataclass
class PipelineForecastApplication:
    service: PipelineForecastService

    def record_snapshot(self, command: RecordPipelineSnapshotCommand) -> None:
        self.service.record_snapshot(command.snapshot)

    def get_snapshots(self, query: GetPipelineSnapshotsQuery) -> list[PipelineSnapshot]:
        return self.service.list_snapshots(query.opportunity_id)

    def create_forecast(self, command: CreateForecastCommand) -> None:
        self.service.create_forecast(command.forecast)

    def get_forecast(self, query: GetForecastQuery) -> SalesForecast:
        return self.service.get_forecast(query.forecast_id)

    def list_forecasts(self, query: ListForecastsQuery) -> list[SalesForecast]:
        return self.service.list_forecasts(query.scope_id)
