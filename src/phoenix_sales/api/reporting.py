"""Application commands and queries for Sales reporting."""

from dataclasses import dataclass
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
from phoenix_sales.services.reporting import ReportingService


@dataclass(frozen=True)
class ListReportValuesQuery:
    report_filter: ReportFilter


@dataclass(frozen=True)
class RecordReportValueCommand:
    value: ReportValue


@dataclass(frozen=True)
class RecordPipelineLeakageCommand:
    snapshot: PipelineLeakageSnapshot


@dataclass(frozen=True)
class ListPipelineLeakageQuery:
    tenant_id: str
    opportunity_id: UUID | None = None
    observed_from: date | None = None
    observed_to: date | None = None


@dataclass(frozen=True)
class RecordTargetActualCommand:
    result: TargetActualVariance


@dataclass(frozen=True)
class ListTargetActualQuery:
    tenant_id: str


@dataclass(frozen=True)
class RecordQuoteConversionCommand:
    result: QuoteConversionResult


@dataclass(frozen=True)
class ListQuoteConversionQuery:
    tenant_id: str


@dataclass(frozen=True)
class RecordForecastAccuracyCommand:
    result: ForecastAccuracyResult


@dataclass(frozen=True)
class ListForecastAccuracyQuery:
    tenant_id: str


class ReportingApplication:
    def __init__(self, service: ReportingService):
        self.service = service

    def list_values(self, query: ListReportValuesQuery):
        return self.service.list_values(query.report_filter)

    def record_value(self, command: RecordReportValueCommand) -> None:
        self.service.record_value(command.value)

    def record_pipeline_leakage(self, command: RecordPipelineLeakageCommand) -> None:
        self.service.record_pipeline_leakage(command.snapshot)

    def list_pipeline_leakage(self, query: ListPipelineLeakageQuery):
        return self.service.list_pipeline_leakage(
            query.tenant_id,
            opportunity_id=query.opportunity_id,
            observed_from=query.observed_from,
            observed_to=query.observed_to,
        )

    def record_target_actual(self, command: RecordTargetActualCommand) -> None:
        self.service.record_target_actual(command.result)

    def list_target_actual(self, query: ListTargetActualQuery):
        return self.service.list_target_actual(query.tenant_id)

    def record_quote_conversion(self, command: RecordQuoteConversionCommand) -> None:
        self.service.record_quote_conversion(command.result)

    def list_quote_conversion(self, query: ListQuoteConversionQuery):
        return self.service.list_quote_conversion(query.tenant_id)

    def record_forecast_accuracy(self, command: RecordForecastAccuracyCommand) -> None:
        self.service.record_forecast_accuracy(command.result)

    def list_forecast_accuracy(self, query: ListForecastAccuracyQuery):
        return self.service.list_forecast_accuracy(query.tenant_id)
