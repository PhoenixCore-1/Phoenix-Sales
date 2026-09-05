from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from phoenix_sales.api.contracts import PermissionContext, RequestContext, TenantContext, UserContext
from phoenix_sales.api.pipeline_forecast import (
    CreateForecastCommand, GetForecastQuery, GetPipelineSnapshotsQuery,
    ListForecastsQuery, PipelineForecastApplication, RecordPipelineSnapshotCommand,
)
from phoenix_sales.domain.pipeline_forecast import ForecastCategory, ForecastPeriodType, PipelineSnapshot, SalesForecast
from phoenix_sales.persistence.pipeline_forecast_repository import InMemoryPipelineForecastRepository
from phoenix_sales.services.pipeline_forecast import PipelineForecastService


def ctx(*permissions: str, tenant: str = "t1"):
    return RequestContext(TenantContext(tenant), UserContext("u1"), PermissionContext(frozenset(permissions)))


def forecast(tenant="t1"):
    return SalesForecast(tenant, date(2026,1,1), date(2026,1,31), ForecastPeriodType.MONTH, "rep-1", ForecastCategory.COMMIT, Decimal("1000"), "ZAR")


def test_create_get_and_list_forecast():
    repo = InMemoryPipelineForecastRepository()
    app = PipelineForecastApplication(PipelineForecastService(ctx("sales.forecast.create", "sales.forecast.read"), repo))
    item = forecast()
    app.create_forecast(CreateForecastCommand(item))
    assert app.get_forecast(GetForecastQuery(item.id)) is item
    assert app.list_forecasts(ListForecastsQuery("rep-1")) == [item]


def test_snapshot_is_tenant_scoped():
    repo = InMemoryPipelineForecastRepository()
    oid = uuid4()
    repo.save_snapshot(PipelineSnapshot("t1", oid, "QUOTE", Decimal("50"), Decimal("100")))
    assert repo.list_snapshots("t2", oid) == []


def test_permissions_are_enforced():
    repo = InMemoryPipelineForecastRepository()
    service = PipelineForecastService(ctx(), repo)
    with pytest.raises(PermissionError):
        service.create_forecast(forecast())
    with pytest.raises(PermissionError):
        service.record_snapshot(PipelineSnapshot("t1", uuid4(), "NEW", Decimal("50"), Decimal("100")))


def test_cross_tenant_write_is_rejected():
    service = PipelineForecastService(ctx("sales.forecast.create"), InMemoryPipelineForecastRepository())
    with pytest.raises(PermissionError):
        service.create_forecast(forecast("t2"))


def test_update_and_locked_forecast():
    repo = InMemoryPipelineForecastRepository()
    service = PipelineForecastService(ctx("sales.forecast.create", "sales.forecast.read", "sales.forecast.update"), repo)
    item = forecast()
    service.create_forecast(item)
    service.update_forecast(item.id, forecast_value=Decimal("2000"))
    assert service.get_forecast(item.id).forecast_value == Decimal("2000")
    item.category = ForecastCategory.WON
    with pytest.raises(ValueError):
        service.update_forecast(item.id, forecast_value=Decimal("3000"))
