"""Sales pipeline and forecasting domain foundation for Phoenix Sales V1.0."""

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4


class ForecastCategory(str, Enum):
    PIPELINE = "PIPELINE"
    BEST_CASE = "BEST_CASE"
    COMMIT = "COMMIT"
    WON = "WON"
    LOST = "LOST"


class ForecastPeriodType(str, Enum):
    MONTH = "MONTH"
    QUARTER = "QUARTER"
    YEAR = "YEAR"


class PipelineOutcome(str, Enum):
    OPEN = "OPEN"
    WON = "WON"
    LOST = "LOST"
    NO_DECISION = "NO_DECISION"
    DEFERRED = "DEFERRED"
    CANCELLED = "CANCELLED"
    NURTURE = "NURTURE"


@dataclass(frozen=True)
class PipelineSnapshot:
    """Point-in-time commercial pipeline observation."""

    tenant_id: str
    opportunity_id: UUID
    stage: str
    probability: Decimal
    estimated_value: Decimal
    solution_value: Decimal = Decimal("0")
    quote_value: Decimal = Decimal("0")
    order_value: Decimal = Decimal("0")
    revenue_value: Decimal = Decimal("0")
    snapshot_date: date = field(default_factory=date.today)

    def __post_init__(self) -> None:
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not 0 <= self.probability <= 100:
            raise ValueError("probability must be between 0 and 100")
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
    def weighted_value(self) -> Decimal:
        return self.estimated_value * self.probability / Decimal("100")


@dataclass
class SalesForecast:
    """Expected commercial result for a defined period and scope."""

    tenant_id: str
    period_start: date
    period_end: date
    period_type: ForecastPeriodType
    scope_id: str
    category: ForecastCategory
    forecast_value: Decimal
    currency: str
    owner_id: str | None = None
    id: UUID = field(default_factory=uuid4)
    confidence: Decimal | None = None
    notes: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if self.period_end < self.period_start:
            raise ValueError("period_end cannot be before period_start")
        if not self.scope_id.strip():
            raise ValueError("scope_id is required")
        if not self.currency.strip():
            raise ValueError("currency is required")
        if self.forecast_value < 0:
            raise ValueError("forecast_value cannot be negative")
        if self.confidence is not None and not 0 <= self.confidence <= 100:
            raise ValueError("confidence must be between 0 and 100")

    @property
    def is_locked(self) -> bool:
        return self.category in {ForecastCategory.WON, ForecastCategory.LOST}
