"""Opportunity domain model for Phoenix Sales V1.0."""

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4


class OpportunityStage(str, Enum):
    """Controlled Sales opportunity stages."""

    NEW = "NEW"
    QUALIFIED = "QUALIFIED"
    DISCOVERY = "DISCOVERY"
    SOLUTION_DEVELOPMENT = "SOLUTION_DEVELOPMENT"
    QUOTE = "QUOTE"
    NEGOTIATION = "NEGOTIATION"
    WON = "WON"
    LOST = "LOST"
    NO_DECISION = "NO_DECISION"
    DEFERRED = "DEFERRED"
    CANCELLED = "CANCELLED"
    NURTURE = "NURTURE"


TERMINAL_STAGES = frozenset(
    {
        OpportunityStage.WON,
        OpportunityStage.LOST,
        OpportunityStage.NO_DECISION,
        OpportunityStage.DEFERRED,
        OpportunityStage.CANCELLED,
        OpportunityStage.NURTURE,
    }
)


@dataclass
class Opportunity:
    """Sales-owned commercial opportunity.

    Customer and contact identifiers are references to objects owned by other
    modules; Sales does not duplicate their master data.
    """

    tenant_id: str
    name: str
    customer_id: str
    owner_user_id: str
    id: UUID = field(default_factory=uuid4)
    contact_id: str | None = None
    requirement: str | None = None
    application: str | None = None
    estimated_value: Decimal | None = None
    estimated_margin: Decimal | None = None
    close_date: date | None = None
    stage: OpportunityStage = OpportunityStage.NEW
    probability: Decimal = Decimal("0")
    source: str | None = None
    project_id: str | None = None
    competitor: str | None = None
    current_solution: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        for value, field_name in (
            (self.tenant_id, "tenant_id"),
            (self.name, "name"),
            (self.customer_id, "customer_id"),
            (self.owner_user_id, "owner_user_id"),
        ):
            if not value or not value.strip():
                raise ValueError(f"{field_name} is required")

        if not Decimal("0") <= self.probability <= Decimal("100"):
            raise ValueError("probability must be between 0 and 100")

        if self.estimated_value is not None and self.estimated_value < 0:
            raise ValueError("estimated_value cannot be negative")

        if self.estimated_margin is not None and self.estimated_margin < 0:
            raise ValueError("estimated_margin cannot be negative")

    @property
    def is_terminal(self) -> bool:
        return self.stage in TERMINAL_STAGES

    def transition_to(self, stage: OpportunityStage) -> None:
        """Move the opportunity to a new controlled stage."""
        if self.is_terminal:
            raise ValueError("terminal opportunity cannot be transitioned")

        if stage == OpportunityStage.NEW and self.stage != OpportunityStage.NEW:
            raise ValueError("opportunity cannot return to NEW")

        self.stage = stage
        self.updated_at = datetime.now(timezone.utc)

    def set_probability(self, probability: Decimal) -> None:
        """Set probability independently of stage."""
        probability = Decimal(probability)
        if not Decimal("0") <= probability <= Decimal("100"):
            raise ValueError("probability must be between 0 and 100")
        self.probability = probability
        self.updated_at = datetime.now(timezone.utc)
