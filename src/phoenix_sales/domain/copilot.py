"""Sales Copilot domain contracts.

The Copilot is provider-independent. It defines Sales intent, context and
response semantics while Phoenix Core supplies the underlying AI service.
"""

from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4


class CopilotIntent(str, Enum):
    ASK = "ASK"
    SUMMARIZE = "SUMMARIZE"
    EXPLAIN = "EXPLAIN"
    IDENTIFY_MISSING_INFORMATION = "IDENTIFY_MISSING_INFORMATION"
    RECOMMEND = "RECOMMEND"


class CopilotAuthority(str, Enum):
    INFORM = "INFORM"
    RECOMMEND = "RECOMMEND"
    DRAFT = "DRAFT"
    EXECUTE_WITH_CONFIRMATION = "EXECUTE_WITH_CONFIRMATION"
    RESTRICTED = "RESTRICTED"


@dataclass(frozen=True)
class SalesCopilotContext:
    tenant_id: str
    user_id: str
    opportunity_id: UUID | None = None
    customer_id: str | None = None
    quote_id: UUID | None = None
    sales_order_id: UUID | None = None
    facts: tuple[str, ...] = ()
    permitted_data: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.tenant_id.strip() or not self.user_id.strip():
            raise ValueError("tenant_id and user_id are required")
        if any(not fact.strip() for fact in self.facts):
            raise ValueError("facts cannot contain blank values")
        if any(not item.strip() for item in self.permitted_data):
            raise ValueError("permitted_data cannot contain blank values")


@dataclass(frozen=True)
class CopilotRequest:
    context: SalesCopilotContext
    prompt: str
    intent: CopilotIntent = CopilotIntent.ASK
    requested_authority: CopilotAuthority = CopilotAuthority.INFORM
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.prompt.strip():
            raise ValueError("prompt is required")


@dataclass(frozen=True)
class CopilotRecommendation:
    title: str
    rationale: str
    confidence: float
    authority: CopilotAuthority = CopilotAuthority.RECOMMEND
    action: str | None = None

    def __post_init__(self) -> None:
        if not self.title.strip() or not self.rationale.strip():
            raise ValueError("title and rationale are required")
        if not 0 <= self.confidence <= 100:
            raise ValueError("confidence must be between 0 and 100")
        if self.authority is CopilotAuthority.EXECUTE_WITH_CONFIRMATION and not self.action:
            raise ValueError("execution recommendations require an action")
        if self.authority is CopilotAuthority.RESTRICTED and self.action:
            raise ValueError("restricted recommendations cannot contain an executable action")


@dataclass(frozen=True)
class CopilotResponse:
    request_id: UUID
    answer: str
    recommendations: tuple[CopilotRecommendation, ...] = ()
    sources: tuple[str, ...] = ()
    requires_confirmation: bool = False

    def __post_init__(self) -> None:
        if not self.answer.strip():
            raise ValueError("answer is required")
        if self.requires_confirmation and not any(
            r.authority is CopilotAuthority.EXECUTE_WITH_CONFIRMATION for r in self.recommendations
        ):
            raise ValueError("confirmation requires an executable recommendation")
