"""Persistence boundary for Sales pipeline snapshots and forecasts."""
from __future__ import annotations

from typing import Protocol
from uuid import UUID

from phoenix_sales.domain.pipeline_forecast import PipelineSnapshot, SalesForecast


class PipelineForecastRepository(Protocol):
    def save_snapshot(self, snapshot: PipelineSnapshot) -> None: ...
    def list_snapshots(self, tenant_id: str, opportunity_id: UUID) -> list[PipelineSnapshot]: ...
    def save_forecast(self, forecast: SalesForecast) -> None: ...
    def get_forecast(self, tenant_id: str, forecast_id: UUID) -> SalesForecast | None: ...
    def list_forecasts(self, tenant_id: str, scope_id: str) -> list[SalesForecast]: ...


class InMemoryPipelineForecastRepository:
    def __init__(self) -> None:
        self._snapshots: dict[tuple[str, UUID, object], PipelineSnapshot] = {}
        self._forecasts: dict[tuple[str, UUID], SalesForecast] = {}

    def save_snapshot(self, snapshot: PipelineSnapshot) -> None:
        key = (snapshot.tenant_id, snapshot.opportunity_id, snapshot.snapshot_date)
        self._snapshots[key] = snapshot

    def list_snapshots(self, tenant_id: str, opportunity_id: UUID) -> list[PipelineSnapshot]:
        return [s for (t, o, _), s in self._snapshots.items() if t == tenant_id and o == opportunity_id]

    def save_forecast(self, forecast: SalesForecast) -> None:
        self._forecasts[(forecast.tenant_id, forecast.id)] = forecast

    def get_forecast(self, tenant_id: str, forecast_id: UUID) -> SalesForecast | None:
        return self._forecasts.get((tenant_id, forecast_id))

    def list_forecasts(self, tenant_id: str, scope_id: str) -> list[SalesForecast]:
        return [f for (t, _), f in self._forecasts.items() if t == tenant_id and f.scope_id == scope_id]
