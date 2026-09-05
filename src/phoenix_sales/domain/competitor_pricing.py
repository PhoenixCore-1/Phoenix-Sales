"""Competitor Pricing Intelligence domain for Phoenix Sales V1.0."""

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4


class CompetitorPricingSource(str, Enum):
    CUSTOMER = "CUSTOMER"
    SALES_REP = "SALES_REP"
    QUOTE = "QUOTE"
    MARKET = "MARKET"
    OTHER = "OTHER"


class CompetitorPricingValidity(str, Enum):
    CURRENT = "CURRENT"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"


@dataclass
class CompetitorPriceObservation:
    tenant_id: str
    competitor: str
    competitor_product: str
    comparable_product_id: str
    competitor_price: Decimal
    currency: str
    observed_date: date
    quantity: Decimal = Decimal("1")
    customer_id: str | None = None
    project_id: str | None = None
    region: str | None = None
    source: CompetitorPricingSource = CompetitorPricingSource.OTHER
    validity: CompetitorPricingValidity = CompetitorPricingValidity.UNKNOWN
    confidence: Decimal = Decimal("0")
    notes: str | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.competitor.strip() or not self.competitor_product.strip():
            raise ValueError("competitor and competitor_product are required")
        if not self.comparable_product_id.strip():
            raise ValueError("comparable_product_id is required")
        if self.competitor_price < 0:
            raise ValueError("competitor_price cannot be negative")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        if not self.currency.strip():
            raise ValueError("currency is required")
        if not 0 <= self.confidence <= 100:
            raise ValueError("confidence must be between 0 and 100")

    @property
    def unit_price(self) -> Decimal:
        return self.competitor_price / self.quantity
