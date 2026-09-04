"""Solution Engine domain model for Phoenix Sales V1.0."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class SolutionStatus(str, Enum):
    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    SUPERSEDED = "SUPERSEDED"
    CANCELLED = "CANCELLED"


class SolutionComponentType(str, Enum):
    PRODUCT = "PRODUCT"
    SERVICE = "SERVICE"
    ACCESSORY = "ACCESSORY"
    LABOUR = "LABOUR"
    EQUIPMENT = "EQUIPMENT"
    CONSUMABLE = "CONSUMABLE"


@dataclass(frozen=True)
class SolutionComponent:
    """A manufacturer-agnostic component of a proposed solution."""

    component_type: SolutionComponentType
    item_id: str
    description: str
    quantity: float
    unit: str = "EA"
    alternative_group: str | None = None
    is_recommended: bool = False

    def __post_init__(self) -> None:
        if not self.item_id.strip():
            raise ValueError("item_id is required")
        if not self.description.strip():
            raise ValueError("description is required")
        if self.quantity <= 0:
            raise ValueError("quantity must be greater than zero")
        if not self.unit.strip():
            raise ValueError("unit is required")


@dataclass
class Solution:
    """Structured representation of how a customer requirement is solved."""

    tenant_id: str
    opportunity_id: UUID
    name: str
    requirement: str
    application: str
    id: UUID = field(default_factory=uuid4)
    version: int = 1
    project_id: str | None = None
    site_id: str | None = None
    technical_parameters: dict[str, str] = field(default_factory=dict)
    constraints: list[str] = field(default_factory=list)
    compliance_requirements: list[str] = field(default_factory=list)
    components: list[SolutionComponent] = field(default_factory=list)
    technical_rationale: str | None = None
    commercial_rationale: str | None = None
    status: SolutionStatus = SolutionStatus.DRAFT
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.name.strip():
            raise ValueError("name is required")
        if not self.requirement.strip():
            raise ValueError("requirement is required")
        if not self.application.strip():
            raise ValueError("application is required")
        if self.version < 1:
            raise ValueError("version must be at least 1")

    @property
    def is_locked(self) -> bool:
        return self.status in {
            SolutionStatus.APPROVED,
            SolutionStatus.SUPERSEDED,
            SolutionStatus.CANCELLED,
        }

    def add_component(self, component: SolutionComponent) -> None:
        if self.is_locked:
            raise ValueError("locked solution cannot be changed")
        self.components.append(component)
        self.updated_at = datetime.now(timezone.utc)

    def submit_for_review(self) -> None:
        if self.status is not SolutionStatus.DRAFT:
            raise ValueError("only draft solutions can be submitted")
        if not self.components:
            raise ValueError("solution requires at least one component")
        self.status = SolutionStatus.IN_REVIEW
        self.updated_at = datetime.now(timezone.utc)

    def approve(self) -> None:
        if self.status is not SolutionStatus.IN_REVIEW:
            raise ValueError("only solutions in review can be approved")
        if not self.components:
            raise ValueError("solution requires at least one component")
        self.status = SolutionStatus.APPROVED
        self.updated_at = datetime.now(timezone.utc)

    def cancel(self) -> None:
        if self.is_locked:
            raise ValueError("solution is already closed")
        self.status = SolutionStatus.CANCELLED
        self.updated_at = datetime.now(timezone.utc)
