from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from phoenix_sales.domain.reporting import (
    ForecastAccuracyResult,
    PipelineLeakageSnapshot,
    PipelineLeakageStage,
    QuoteConversionResult,
    ReportFilter,
    ReportValue,
    SalesReportDimension,
    SalesReportMetric,
    TargetActualVariance,
)


def test_report_filter_validates_tenant_and_period():
    result = ReportFilter(
        tenant_id="t1",
        period_start=date(2026, 9, 1),
        period_end=date(2026, 9, 30),
        dimensions=(SalesReportDimension.BRANCH, SalesReportDimension.SALESPERSON),
        scope_ids=("branch-1",),
        currency="ZAR",
    )
    assert result.tenant_id == "t1"


def test_report_filter_rejects_invalid_period():
    with pytest.raises(ValueError, match="period_end"):
        ReportFilter(
            tenant_id="t1",
            period_start=date(2026, 9, 30),
            period_end=date(2026, 9, 1),
        )


def test_report_value_requires_matching_dimension_id():
    with pytest.raises(ValueError, match="dimension_id"):
        ReportValue(
            tenant_id="t1",
            metric=SalesReportMetric.REVENUE,
            value=Decimal("100"),
            dimension=SalesReportDimension.BRANCH,
        )


def test_report_value_rejects_negative_value():
    with pytest.raises(ValueError, match="cannot be negative"):
        ReportValue(
            tenant_id="t1",
            metric=SalesReportMetric.REVENUE,
            value=Decimal("-1"),
        )


def test_pipeline_leakage_values_and_ratio():
    snapshot = PipelineLeakageSnapshot(
        tenant_id="t1",
        opportunity_id=uuid4(),
        estimated_value=Decimal("1000"),
        solution_value=Decimal("900"),
        quote_value=Decimal("800"),
        order_value=Decimal("700"),
        revenue_value=Decimal("600"),
    )
    assert snapshot.values[PipelineLeakageStage.QUOTE_VALUE] == Decimal("800")
    assert snapshot.estimated_to_revenue_ratio == Decimal("60")


def test_pipeline_leakage_zero_estimate_is_safe():
    snapshot = PipelineLeakageSnapshot(
        tenant_id="t1",
        opportunity_id=uuid4(),
        estimated_value=Decimal("0"),
    )
    assert snapshot.estimated_to_revenue_ratio == Decimal("0")


def test_target_actual_variance_and_attainment():
    result = TargetActualVariance(
        tenant_id="t1",
        target_value=Decimal("1000"),
        actual_value=Decimal("900"),
        period_start=date(2026, 9, 1),
        period_end=date(2026, 9, 30),
        metric=SalesReportMetric.REVENUE,
        currency="ZAR",
    )
    assert result.variance == Decimal("-100")
    assert result.attainment_percent == Decimal("90")


def test_quote_conversion():
    result = QuoteConversionResult(
        tenant_id="t1",
        quoted_count=20,
        accepted_count=8,
        period_start=date(2026, 9, 1),
        period_end=date(2026, 9, 30),
    )
    assert result.conversion_percent == Decimal("40")


def test_quote_conversion_rejects_more_acceptances_than_quotes():
    with pytest.raises(ValueError, match="accepted_count"):
        QuoteConversionResult(
            tenant_id="t1",
            quoted_count=2,
            accepted_count=3,
            period_start=date(2026, 9, 1),
            period_end=date(2026, 9, 30),
        )


def test_forecast_accuracy():
    result = ForecastAccuracyResult(
        tenant_id="t1",
        forecast_value=Decimal("900"),
        actual_value=Decimal("1000"),
        period_start=date(2026, 9, 1),
        period_end=date(2026, 9, 30),
        scope_id="sales-team-1",
        currency="ZAR",
    )
    assert result.variance == Decimal("100")
    assert result.accuracy_percent == Decimal("90")


def test_forecast_accuracy_exact_match():
    result = ForecastAccuracyResult(
        tenant_id="t1",
        forecast_value=Decimal("0"),
        actual_value=Decimal("0"),
        period_start=date(2026, 9, 1),
        period_end=date(2026, 9, 30),
        scope_id="sales-team-1",
        currency="ZAR",
    )
    assert result.accuracy_percent == Decimal("100")
