"""Sales reporting and analytics domain foundation for Phoenix Sales V1.0.

Reporting is read-only and consumes authoritative Sales domain/read-model data.
It does not own transactional business records or duplicate source-of-truth data.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4


class SalesReportMetric(str, Enum):
    REVENUE = "REVENUE"
    GROSS_PROFIT = "GROSS_PROFIT"
    MARGIN = "MARGIN"
    PIPELINE_VALUE = "PIPELINE_VALUE"
    WEIGHTED_PIPELINE = "WEIGHTED_PIPELINE"
    QUOTE_VALUE = "QUOTE_VALUE"
    ORDER_VALUE = "ORDER_VALUE"
    QUOTE_CONVERSION = "QUOTE_CONVERSION"
    TARGET = "TARGET"
    ACTUAL = "ACTUAL"
    FORECAST = "FORECAST"
    FORECAST_ACCURACY = "FORECAST_ACCURACY"
    COMPETITOR_PRICE = "COMPETITOR_PRICE"


class SalesReportDimension(str, Enum):
    COMPANY = "COMPANY"
    REGION = "REGION"
    BRANCH = "BRANCH"
    TEAM = "TEAM"
    SALESPERSON = "SALESPERSON"
    TERRITORY = "TERRITORY"
    CUSTOMER = "CUSTOMER"
    CUSTOMER_SEGMENT = "CUSTOMER_SEGMENT"
    PRODUCT = "PRODUCT"
    PRODUCT_CATEGORY = "PRODUCT_CATEGORY"
    OPPORTUNITY_STAGE = "OPPORTUNITY_STAGE"
    FORECAST_CATEGORY = "FORECAST_CATEGORY"
    PERIOD = "PERIOD"


class PipelineLeakageStage(str, Enum):
    ESTIMATED_VALUE = "ESTIMATED_VALUE"
    SOLUTION_VALUE = "SOLUTION_VALUE"
    QUOTE_VALUE = "QUOTE_VALUE"
    ORDER_VALUE = "ORDER_VALUE"
    REVENUE_VALUE = "REVENUE_VALUE"


@dataclass(frozen=True)
class ReportFilter:
    """Tenant-scoped, read-only reporting filter."""

    tenant_id: str
    period_start: date | None = None
    period_end: date | None = None
    dimensions: tuple[SalesReportDimension, ...] = ()
    scope_ids: tuple[str, ...] = ()
    currency: str | None = None

    def __post_init__(self) -> None:
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if self.period_start and self.period_end and self.period_end < self.period_start:
            raise ValueError("period_end cannot be before period_start")
        if self.currency is not None and not self.currency.strip():
            raise ValueError("currency cannot be blank")
        if any(not value.strip() for value in self.scope_ids):
            raise ValueError("scope_ids cannot contain blank values")


@dataclass(frozen=True)
class ReportValue:
    """A single aggregated reporting value for a dimension bucket."""

    tenant_id: str
    metric: SalesReportMetric
    value: Decimal
    dimension: SalesReportDimension | None = None
    dimension_id: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    currency: str | None = None

    def __post_init__(self) -> None:
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if self.value < 0:
            raise ValueError("value cannot be negative")
        if self.period_start and self.period_end and self.period_end < self.period_start:
            raise ValueError("period_end cannot be before period_start")
        if self.dimension is None and self.dimension_id is not None:
            raise ValueError("dimension is required when dimension_id is provided")
        if self.dimension is not None and self.dimension_id is None:
            raise ValueError("dimension_id is required when dimension is provided")
        if self.currency is not None and not self.currency.strip():
            raise ValueError("currency cannot be blank")


@dataclass(frozen=True)
class PipelineLeakageSnapshot:
    """Point-in-time value progression used to expose commercial leakage."""

    tenant_id: str
    opportunity_id: UUID
    estimated_value: Decimal
    solution_value: Decimal = Decimal("0")
    quote_value: Decimal = Decimal("0")
    order_value: Decimal = Decimal("0")
    revenue_value: Decimal = Decimal("0")
    snapshot_date: date = field(default_factory=date.today)

    def __post_init__(self) -> None:
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        for name, value in (
            ("estimated_value", self.estimated_value),
            ("solution_value", self.solution_value),
            ("quote_value", self.quote_value),
            ("order_value", self.order_value),
            ("revenue_value", self.revenue_value),
        ):
            if value < 0:
                raise ValueError(f"{name} cannot be negative")

    @property
    def values(self) -> dict[PipelineLeakageStage, Decimal]:
        return {
            PipelineLeakageStage.ESTIMATED_VALUE: self.estimated_value,
            PipelineLeakageStage.SOLUTION_VALUE: self.solution_value,
            PipelineLeakageStage.QUOTE_VALUE: self.quote_value,
            PipelineLeakageStage.ORDER_VALUE: self.order_value,
            PipelineLeakageStage.REVENUE_VALUE: self.revenue_value,
        }

    @property
    def estimated_to_revenue_ratio(self) -> Decimal:
        if self.estimated_value == 0:
            return Decimal("0")
        return self.revenue_value / self.estimated_value * Decimal("100")


@dataclass(frozen=True)
class TargetActualVariance:
    """Read-only target versus actual result."""

    tenant_id: str
    target_value: Decimal
    actual_value: Decimal
    period_start: date
    period_end: date
    metric: SalesReportMetric
    currency: str | None = None
    scope_id: str | None = None

    def __post_init__(self) -> None:
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if self.period_end < self.period_start:
            raise ValueError("period_end cannot be before period_start")
        if self.target_value < 0 or self.actual_value < 0:
            raise ValueError("target_value and actual_value cannot be negative")
        if self.currency is not None and not self.currency.strip():
            raise ValueError("currency cannot be blank")

    @property
    def variance(self) -> Decimal:
        return self.actual_value - self.target_value

    @property
    def attainment_percent(self) -> Decimal:
        if self.target_value == 0:
            return Decimal("0")
        return self.actual_value / self.target_value * Decimal("100")


@dataclass(frozen=True)
class QuoteConversionResult:
    """Read-only quote conversion result for a reporting period."""

    tenant_id: str
    quoted_count: int
    accepted_count: int
    period_start: date
    period_end: date

    def __post_init__(self) -> None:
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if self.period_end < self.period_start:
            raise ValueError("period_end cannot be before period_start")
        if self.quoted_count < 0 or self.accepted_count < 0:
            raise ValueError("quote counts cannot be negative")
        if self.accepted_count > self.quoted_count:
            raise ValueError("accepted_count cannot exceed quoted_count")

    @property
    def conversion_percent(self) -> Decimal:
        if self.quoted_count == 0:
            return Decimal("0")
        return Decimal(self.accepted_count) / Decimal(self.quoted_count) * Decimal("100")


@dataclass(frozen=True)
class ForecastAccuracyResult:
    """Read-only forecast accuracy result."""

    tenant_id: str
    forecast_value: Decimal
    actual_value: Decimal
    period_start: date
    period_end: date
    scope_id: str
    currency: str
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.scope_id.strip():
            raise ValueError("scope_id is required")
        if not self.currency.strip():
            raise ValueError("currency is required")
        if self.period_end < self.period_start:
            raise ValueError("period_end cannot be before period_start")
        if self.forecast_value < 0 or self.actual_value < 0:
            raise ValueError("forecast_value and actual_value cannot be negative")

    @property
    def variance(self) -> Decimal:
        return self.actual_value - self.forecast_value

    @property
    def accuracy_percent(self) -> Decimal:
        if self.actual_value == 0:
            return Decimal("0") if self.forecast_value else Decimal("100")
        error = abs(self.actual_value - self.forecast_value) / self.actual_value * Decimal("100")
        return max(Decimal("0"), Decimal("100") - error)
