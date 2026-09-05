"""Margin rule domain for Phoenix Sales V1.0."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class MarginStatus(str, Enum):
    ACCEPTABLE = "ACCEPTABLE"
    WARNING = "WARNING"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class MarginRule:
    """Tenant-configurable minimum-margin rule."""

    minimum_margin_percent: Decimal
    warning_margin_percent: Decimal | None = None
    product_id: str | None = None
    category_id: str | None = None

    def __post_init__(self) -> None:
        if not Decimal("0") <= self.minimum_margin_percent <= Decimal("100"):
            raise ValueError("minimum_margin_percent must be between 0 and 100")
        if self.warning_margin_percent is not None and not Decimal("0") <= self.warning_margin_percent <= Decimal("100"):
            raise ValueError("warning_margin_percent must be between 0 and 100")
        if self.warning_margin_percent is not None and self.warning_margin_percent < self.minimum_margin_percent:
            raise ValueError("warning_margin_percent cannot be below minimum_margin_percent")
        if self.product_id and self.category_id:
            raise ValueError("rule cannot target both product and category")

    def evaluate(self, margin_percent: Decimal) -> MarginStatus:
        margin_percent = Decimal(margin_percent)
        if margin_percent < self.minimum_margin_percent:
            return MarginStatus.BLOCKED
        if self.warning_margin_percent is not None and margin_percent < self.warning_margin_percent:
            return MarginStatus.WARNING
        return MarginStatus.ACCEPTABLE
