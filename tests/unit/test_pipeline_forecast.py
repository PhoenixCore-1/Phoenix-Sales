from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from phoenix_sales.domain.pipeline_forecast import (
    ForecastCategory,
    ForecastPeriodType,
    PipelineSnapshot,
    SalesForecast,
)


def test_pipeline_snapshot_weighted_value():
    snapshot = PipelineSnapshot(
        tenant_id="t1",
        opportunity_id=uuid4(),
        stage="QUALIFIED",
        probability=Decimal("40"),
        estimated_value=Decimal("100000"),
    )
    assert snapshot.weighted_value == Decimal("40000")


def test_pipeline_snapshot_supports_value_leakage_chain():
    snapshot = PipelineSnapshot(
        tenant_id="t1",
        opportunity_id=uuid4(),
        stage="QUOTE",
        probability=Decimal("75"),
        estimated_value=Decimal("100000"),
        solution_value=Decimal("90000"),
        quote_value=Decimal("85000"),
        order_value=Decimal("0"),
        revenue_value=Decimal("0"),
    )
    assert snapshot.solution_value == Decimal("90000")
    assert snapshot.quote_value == Decimal("85000")


def test_pipeline_snapshot_rejects_invalid_probability():
    with pytest.raises(ValueError):
        PipelineSnapshot("t1", uuid4(), "NEW", Decimal("101"), Decimal("1"))


def test_pipeline_snapshot_rejects_negative_value():
    with pytest.raises(ValueError):
        PipelineSnapshot("t1", uuid4(), "NEW", Decimal("50"), Decimal("-1"))


def test_sales_forecast_creation():
    forecast = SalesForecast(
        tenant_id="t1",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 3, 31),
        period_type=ForecastPeriodType.QUARTER,
        scope_id="branch-jhb",
        category=ForecastCategory.COMMIT,
        forecast_value=Decimal("500000"),
        currency="ZAR",
        confidence=Decimal("85"),
    )
    assert forecast.category is ForecastCategory.COMMIT
    assert forecast.is_locked is False


def test_forecast_confidence_bounds():
    with pytest.raises(ValueError):
        SalesForecast(
            "t1", date(2026, 1, 1), date(2026, 1, 31),
            ForecastPeriodType.MONTH, "rep-1", ForecastCategory.PIPELINE,
            Decimal("100"), "ZAR", confidence=Decimal("101")
        )


def test_forecast_period_must_be_valid():
    with pytest.raises(ValueError):
        SalesForecast(
            "t1", date(2026, 2, 1), date(2026, 1, 31),
            ForecastPeriodType.MONTH, "rep-1", ForecastCategory.PIPELINE,
            Decimal("100"), "ZAR"
        )
