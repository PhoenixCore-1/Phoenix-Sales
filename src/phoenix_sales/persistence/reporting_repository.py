"""Persistence contract for Sales reporting read models."""

from __future__ import annotations

from datetime import date
from typing import Protocol

from phoenix_sales.domain.reporting import (
    ForecastAccuracyResult,
    PipelineLeakageSnapshot,
    QuoteConversionResult,
    ReportFilter,
    ReportValue,
    TargetActualVariance,
)


class ReportingRepository(Protocol):
    def save_value(self, value: ReportValue) -> None: ...
    def list_values(self, report_filter: ReportFilter) -> list[ReportValue]: ...
    def save_pipeline_leakage(self, snapshot: PipelineLeakageSnapshot) -> None: ...
    def list_pipeline_leakage(
        self,
        tenant_id: str,
        *,
        opportunity_id=None,
        observed_from: date | None = None,
        observed_to: date | None = None,
    ) -> list[PipelineLeakageSnapshot]: ...
    def save_target_actual(self, result: TargetActualVariance) -> None: ...
    def list_target_actual(self, tenant_id: str) -> list[TargetActualVariance]: ...
    def save_quote_conversion(self, result: QuoteConversionResult) -> None: ...
    def list_quote_conversion(self, tenant_id: str) -> list[QuoteConversionResult]: ...
    def save_forecast_accuracy(self, result: ForecastAccuracyResult) -> None: ...
    def list_forecast_accuracy(self, tenant_id: str) -> list[ForecastAccuracyResult]: ...


class InMemoryReportingRepository:
    """Tenant-scoped reference repository for reporting read models."""

    def __init__(self) -> None:
        self._values: list[ReportValue] = []
        self._leakage: list[PipelineLeakageSnapshot] = []
        self._target_actual: list[TargetActualVariance] = []
        self._quote_conversion: list[QuoteConversionResult] = []
        self._forecast_accuracy: list[ForecastAccuracyResult] = []

    @staticmethod
    def _tenant(tenant_id: str) -> str:
        if not tenant_id.strip():
            raise ValueError("tenant_id is required")
        return tenant_id

    def save_value(self, value: ReportValue) -> None:
        self._tenant(value.tenant_id)
        self._values.append(value)

    def list_values(self, report_filter: ReportFilter) -> list[ReportValue]:
        self._tenant(report_filter.tenant_id)
        result = [v for v in self._values if v.tenant_id == report_filter.tenant_id]
        if report_filter.period_start:
            result = [v for v in result if v.period_end is None or v.period_end >= report_filter.period_start]
        if report_filter.period_end:
            result = [v for v in result if v.period_start is None or v.period_start <= report_filter.period_end]
        if report_filter.currency:
            result = [v for v in result if v.currency == report_filter.currency]
        if report_filter.scope_ids:
            result = [v for v in result if v.dimension_id in report_filter.scope_ids]
        return list(result)

    def save_pipeline_leakage(self, snapshot: PipelineLeakageSnapshot) -> None:
        self._tenant(snapshot.tenant_id)
        self._leakage.append(snapshot)

    def list_pipeline_leakage(self, tenant_id: str, *, opportunity_id=None, observed_from=None, observed_to=None):
        self._tenant(tenant_id)
        result = [x for x in self._leakage if x.tenant_id == tenant_id]
        if opportunity_id is not None:
            result = [x for x in result if x.opportunity_id == opportunity_id]
        if observed_from is not None:
            result = [x for x in result if x.snapshot_date >= observed_from]
        if observed_to is not None:
            result = [x for x in result if x.snapshot_date <= observed_to]
        return list(result)

    def save_target_actual(self, result: TargetActualVariance) -> None:
        self._tenant(result.tenant_id)
        self._target_actual.append(result)

    def list_target_actual(self, tenant_id: str) -> list[TargetActualVariance]:
        self._tenant(tenant_id)
        return [x for x in self._target_actual if x.tenant_id == tenant_id]

    def save_quote_conversion(self, result: QuoteConversionResult) -> None:
        self._tenant(result.tenant_id)
        self._quote_conversion.append(result)

    def list_quote_conversion(self, tenant_id: str) -> list[QuoteConversionResult]:
        self._tenant(tenant_id)
        return [x for x in self._quote_conversion if x.tenant_id == tenant_id]

    def save_forecast_accuracy(self, result: ForecastAccuracyResult) -> None:
        self._tenant(result.tenant_id)
        self._forecast_accuracy.append(result)

    def list_forecast_accuracy(self, tenant_id: str) -> list[ForecastAccuracyResult]:
        self._tenant(tenant_id)
        return [x for x in self._forecast_accuracy if x.tenant_id == tenant_id]
