"""Structured context assembly contracts for Sales Copilot."""

from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class ContextSource(str, Enum):
    CUSTOMER = "CUSTOMER"
    OPPORTUNITY = "OPPORTUNITY"
    SOLUTION = "SOLUTION"
    QUOTE = "QUOTE"
    SALES_ORDER = "SALES_ORDER"
    PIPELINE = "PIPELINE"
    TARGET = "TARGET"
    COMPETITOR_PRICING = "COMPETITOR_PRICING"


class FactType(str, Enum):
    KNOWN = "KNOWN"
    MISSING = "MISSING"
    INFERRED = "INFERRED"


@dataclass(frozen=True)
class CopilotFact:
    source: ContextSource
    name: str
    value: str | None
    fact_type: FactType = FactType.KNOWN

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("fact name is required")
        if self.fact_type is FactType.MISSING and self.value is not None:
            raise ValueError("missing facts cannot contain a value")


@dataclass(frozen=True)
class SalesCopilotContextPackage:
    tenant_id: str
    user_id: str
    facts: tuple[CopilotFact, ...] = ()
    source_ids: Mapping[ContextSource, tuple[str, ...]] = None

    def __post_init__(self) -> None:
        if not self.tenant_id.strip() or not self.user_id.strip():
            raise ValueError("tenant_id and user_id are required")
        if self.source_ids is None:
            object.__setattr__(self, "source_ids", {})
        for source, ids in self.source_ids.items():
            if any(not item.strip() for item in ids):
                raise ValueError(f"blank source id for {source.value}")

    def known(self) -> tuple[CopilotFact, ...]:
        return tuple(f for f in self.facts if f.fact_type is FactType.KNOWN)

    def missing(self) -> tuple[CopilotFact, ...]:
        return tuple(f for f in self.facts if f.fact_type is FactType.MISSING)

    def inferred(self) -> tuple[CopilotFact, ...]:
        return tuple(f for f in self.facts if f.fact_type is FactType.INFERRED)
