"""Application service for Sales pipeline snapshots and forecasts."""
from __future__ import annotations

from uuid import UUID

from phoenix_sales.api.contracts import RequestContext
from phoenix_sales.domain.pipeline_forecast import PipelineSnapshot, SalesForecast
from phoenix_sales.persistence.pipeline_forecast_repository import PipelineForecastRepository


class PipelineForecastService:
    CREATE_PERMISSION = "sales.forecast.create"
    READ_PERMISSION = "sales.forecast.read"
    UPDATE_PERMISSION = "sales.forecast.update"
    SNAPSHOT_PERMISSION = "sales.pipeline.snapshot"

    def __init__(self, context: RequestContext, repository: PipelineForecastRepository) -> None:
        self.context = context
        self.repository = repository

    def record_snapshot(self, snapshot: PipelineSnapshot) -> None:
        self._require(self.SNAPSHOT_PERMISSION)
        self._require_tenant(snapshot.tenant_id)
        self.repository.save_snapshot(snapshot)

    def list_snapshots(self, opportunity_id: UUID) -> list[PipelineSnapshot]:
        self._require(self.READ_PERMISSION)
        return self.repository.list_snapshots(self.context.tenant.tenant_id, opportunity_id)

    def create_forecast(self, forecast: SalesForecast) -> None:
        self._require(self.CREATE_PERMISSION)
        self._require_tenant(forecast.tenant_id)
        self.repository.save_forecast(forecast)

    def get_forecast(self, forecast_id: UUID) -> SalesForecast:
        self._require(self.READ_PERMISSION)
        forecast = self.repository.get_forecast(self.context.tenant.tenant_id, forecast_id)
        if forecast is None:
            raise KeyError("forecast not found")
        return forecast

    def list_forecasts(self, scope_id: str) -> list[SalesForecast]:
        self._require(self.READ_PERMISSION)
        return self.repository.list_forecasts(self.context.tenant.tenant_id, scope_id)

    def update_forecast(self, forecast_id: UUID, **changes: object) -> SalesForecast:
        self._require(self.UPDATE_PERMISSION)
        forecast = self.get_forecast(forecast_id)
        if forecast.is_locked:
            raise ValueError("locked forecast cannot be changed")
        protected = {"id", "tenant_id", "created_at"}
        for name, value in changes.items():
            if name in protected:
                raise ValueError(f"cannot change {name}")
            if not hasattr(forecast, name):
                raise ValueError(f"unknown forecast field: {name}")
            setattr(forecast, name, value)
        from datetime import datetime, timezone
        forecast.updated_at = datetime.now(timezone.utc)
        self.repository.save_forecast(forecast)
        return forecast

    def _require_tenant(self, tenant_id: str) -> None:
        if tenant_id != self.context.tenant.tenant_id:
            raise PermissionError("cross-tenant access denied")

    def _require(self, permission: str) -> None:
        if not self.context.has_permission(permission):
            raise PermissionError(f"missing permission: {permission}")
