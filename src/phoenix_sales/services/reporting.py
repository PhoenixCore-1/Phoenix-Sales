"""Application boundary for Sales reporting and analytics."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from phoenix_sales.domain.reporting import (
    ForecastAccuracyResult,
    PipelineLeakageSnapshot,
    QuoteConversionResult,
    ReportFilter,
    ReportValue,
    TargetActualVariance,
)
from phoenix_sales.persistence.reporting_repository import ReportingRepository


class ReportingService:
    READ_PERMISSION = "sales.reporting.read"
    SNAPSHOT_PERMISSION = "sales.reporting.snapshot"

    def __init__(self, context, repository: ReportingRepository):
        self.context = context
        self.repository = repository

    def _require(self, permission: str) -> None:
        if permission not in self.context.permissions.permissions:
            raise PermissionError(f"Missing permission: {permission}")

    def _tenant(self, tenant_id: str) -> None:
        if tenant_id != self.context.tenant.tenant_id:
            raise PermissionError("Cross-tenant access is not permitted")

    def list_values(self, report_filter: ReportFilter) -> list[ReportValue]:
        self._require(self.READ_PERMISSION)
        self._tenant(report_filter.tenant_id)
        return self.repository.list_values(report_filter)

    def record_value(self, value: ReportValue) -> None:
        self._require(self.SNAPSHOT_PERMISSION)
        self._tenant(value.tenant_id)
        self.repository.save_value(value)

    def record_pipeline_leakage(self, snapshot: PipelineLeakageSnapshot) -> None:
        self._require(self.SNAPSHOT_PERMISSION)
        self._tenant(snapshot.tenant_id)
        self.repository.save_pipeline_leakage(snapshot)

    def list_pipeline_leakage(
        self,
        tenant_id: str,
        *,
        opportunity_id: UUID | None = None,
        observed_from: date | None = None,
        observed_to: date | None = None,
    ) -> list[PipelineLeakageSnapshot]:
        self._require(self.READ_PERMISSION)
        self._tenant(tenant_id)
        if observed_from and observed_to and observed_to < observed_from:
            raise ValueError("observed_to cannot be before observed_from")
        return self.repository.list_pipeline_leakage(
            tenant_id,
            opportunity_id=opportunity_id,
            observed_from=observed_from,
            observed_to=observed_to,
        )

    def record_target_actual(self, result: TargetActualVariance) -> None:
        self._require(self.SNAPSHOT_PERMISSION)
        self._tenant(result.tenant_id)
        self.repository.save_target_actual(result)

    def list_target_actual(self, tenant_id: str) -> list[TargetActualVariance]:
        self._require(self.READ_PERMISSION)
        self._tenant(tenant_id)
        return self.repository.list_target_actual(tenant_id)

    def record_quote_conversion(self, result: QuoteConversionResult) -> None:
        self._require(self.SNAPSHOT_PERMISSION)
        self._tenant(result.tenant_id)
        self.repository.save_quote_conversion(result)

    def list_quote_conversion(self, tenant_id: str) -> list[QuoteConversionResult]:
        self._require(self.READ_PERMISSION)
        self._tenant(tenant_id)
        return self.repository.list_quote_conversion(tenant_id)

    def record_forecast_accuracy(self, result: ForecastAccuracyResult) -> None:
        self._require(self.SNAPSHOT_PERMISSION)
        self._tenant(result.tenant_id)
        self.repository.save_forecast_accuracy(result)

    def list_forecast_accuracy(self, tenant_id: str) -> list[ForecastAccuracyResult]:
        self._require(self.READ_PERMISSION)
        self._tenant(tenant_id)
        return self.repository.list_forecast_accuracy(tenant_id)
