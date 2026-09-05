"""Structured opportunity analysis contracts for Sales Copilot."""

from dataclasses import dataclass
from enum import Enum
from typing import Tuple

from phoenix_sales.domain.copilot_context import ContextSource, FactType, SalesCopilotContextPackage


class OpportunityHealth(str, Enum):
    HEALTHY = "HEALTHY"
    AT_RISK = "AT_RISK"
    CRITICAL = "CRITICAL"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"


class OpportunityRiskType(str, Enum):
    STALE = "STALE"
    CLOSE_DATE_RISK = "CLOSE_DATE_RISK"
    EXPIRED_QUOTE = "EXPIRED_QUOTE"
    MISSING_DECISION_MAKER = "MISSING_DECISION_MAKER"
    UNCLEAR_REQUIREMENT = "UNCLEAR_REQUIREMENT"
    COMPETITOR_PRESSURE = "COMPETITOR_PRESSURE"
    LOW_MARGIN = "LOW_MARGIN"
    VALUE_LEAKAGE = "VALUE_LEAKAGE"
    NO_NEXT_ACTION = "NO_NEXT_ACTION"


@dataclass(frozen=True)
class OpportunityRisk:
    risk_type: OpportunityRiskType
    title: str
    detail: str
    severity: int

    def __post_init__(self) -> None:
        if not self.title.strip() or not self.detail.strip():
            raise ValueError("risk title and detail are required")
        if not 1 <= self.severity <= 3:
            raise ValueError("risk severity must be between 1 and 3")


@dataclass(frozen=True)
class OpportunitySignal:
    name: str
    value: str
    fact_type: FactType
    source: ContextSource


@dataclass(frozen=True)
class OpportunityAnalysis:
    tenant_id: str
    user_id: str
    opportunity_id: str
    health: OpportunityHealth
    risks: Tuple[OpportunityRisk, ...] = ()
    missing_information: Tuple[str, ...] = ()
    key_factors: Tuple[OpportunitySignal, ...] = ()
    recommended_actions: Tuple[str, ...] = ()
    confidence: int = 0

    def __post_init__(self) -> None:
        if not self.tenant_id.strip() or not self.user_id.strip() or not self.opportunity_id.strip():
            raise ValueError("tenant_id, user_id and opportunity_id are required")
        if not 0 <= self.confidence <= 100:
            raise ValueError("confidence must be between 0 and 100")

    @classmethod
    def from_context(cls, context: SalesCopilotContextPackage) -> "OpportunityAnalysis":
        opportunity_ids = context.source_ids.get(ContextSource.OPPORTUNITY, ())
        if not opportunity_ids:
            raise ValueError("opportunity source id is required")

        values = {fact.name.lower(): fact for fact in context.facts}
        risks: list[OpportunityRisk] = []
        missing: list[str] = []
        factors: list[OpportunitySignal] = []
        actions: list[str] = []

        def has_value(*names: str) -> bool:
            return any(name.lower() in values and values[name.lower()].value not in (None, "") for name in names)

        if not has_value("decision_maker", "decision maker"):
            missing.append("Decision maker")
            risks.append(OpportunityRisk(OpportunityRiskType.MISSING_DECISION_MAKER, "Decision maker missing", "No decision maker is present in the supplied opportunity context.", 2))
            actions.append("Identify and engage the customer decision maker.")
        if not has_value("requirement", "customer_requirement", "customer requirement"):
            missing.append("Customer requirement")
            risks.append(OpportunityRisk(OpportunityRiskType.UNCLEAR_REQUIREMENT, "Requirement unclear", "The supplied context does not contain a clear customer requirement.", 2))
            actions.append("Confirm the customer requirement and success criteria.")

        for key in ("stage", "probability", "estimated_value", "solution_value", "quote_value", "order_value", "quote_status", "quote_expiry", "competitor", "margin", "last_activity", "next_action", "requirement", "customer_requirement"):
            fact = values.get(key)
            if fact and fact.value is not None:
                factors.append(OpportunitySignal(fact.name, fact.value, fact.fact_type, fact.source))

        quote_status = values.get("quote_status")
        if quote_status and quote_status.value.upper() == "EXPIRED":
            risks.append(OpportunityRisk(OpportunityRiskType.EXPIRED_QUOTE, "Quote expired", "The supplied quote status is expired.", 3))
            actions.append("Re-engage the customer and issue a controlled quote revision if still required.")

        competitor = values.get("competitor")
        if competitor and competitor.value:
            risks.append(OpportunityRisk(OpportunityRiskType.COMPETITOR_PRESSURE, "Competitor present", f"Competitor context is recorded: {competitor.value}.", 2))
            actions.append("Confirm the competitor position and strengthen the value case.")

        margin = values.get("margin")
        if margin and margin.value:
            try:
                if float(margin.value) < 0:
                    raise ValueError
                if float(margin.value) < 15:
                    risks.append(OpportunityRisk(OpportunityRiskType.LOW_MARGIN, "Low margin", "The supplied margin is below the 15% analysis threshold.", 2))
                    actions.append("Review pricing and margin before further commercial commitment.")
            except ValueError:
                pass

        estimated = values.get("estimated_value")
        order = values.get("order_value")
        if estimated and order:
            try:
                e, o = float(estimated.value), float(order.value)
                if e > 0 and o < e * 0.5:
                    risks.append(OpportunityRisk(OpportunityRiskType.VALUE_LEAKAGE, "Value leakage", "Order value is materially below the estimated opportunity value.", 2))
                    actions.append("Review the value leakage between the opportunity and current order position.")
            except ValueError:
                pass

        if not has_value("next_action", "next action"):
            risks.append(OpportunityRisk(OpportunityRiskType.NO_NEXT_ACTION, "No next action", "No next action is present in the supplied context.", 2))
            actions.append("Define and schedule the next customer-facing action.")

        if not has_value("last_activity", "last activity"):
            risks.append(OpportunityRisk(OpportunityRiskType.STALE, "Activity history missing", "Recent activity cannot be established from the supplied context.", 1))
            missing.append("Recent activity")

        # Insufficient information means there is effectively no usable known
        # context to assess the opportunity. Missing fields alone do not make
        # an opportunity information-insufficient when meaningful known facts
        # are available (for example, a known customer requirement).
        known_facts = [
            fact for fact in context.facts
            if fact.fact_type is FactType.KNOWN and fact.value not in (None, "")
        ]
        if not known_facts and len(missing) >= 2:
            health = OpportunityHealth.INSUFFICIENT_INFORMATION
        elif any(r.severity == 3 for r in risks):
            health = OpportunityHealth.CRITICAL
        elif len(risks) >= 2:
            health = OpportunityHealth.AT_RISK
        else:
            health = OpportunityHealth.HEALTHY

        confidence = max(20, min(95, 100 - len(missing) * 12 - len(risks) * 5))
        return cls(context.tenant_id, context.user_id, opportunity_ids[0], health, tuple(risks), tuple(dict.fromkeys(missing)), tuple(factors), tuple(dict.fromkeys(actions)), confidence)
