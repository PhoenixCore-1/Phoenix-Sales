"""Context assembly boundary for Sales Copilot.

Domain repositories remain behind provider-specific ports. The assembler only
combines data the caller is permitted to expose to the Copilot.
"""

from phoenix_sales.domain.copilot_context import (
    ContextSource,
    CopilotFact,
    FactType,
    SalesCopilotContextPackage,
)


class SalesContextProvider:
    """Port for a Sales-owned context source."""

    def facts(self, *, tenant_id: str, entity_id: str) -> tuple[CopilotFact, ...]:
        raise NotImplementedError


class SalesCopilotContextAssembler:
    def __init__(self, providers: dict[ContextSource, SalesContextProvider]) -> None:
        self.providers = providers

    def assemble(self, *, tenant_id: str, user_id: str, entity_ids: dict[ContextSource, str]) -> SalesCopilotContextPackage:
        if not tenant_id.strip() or not user_id.strip():
            raise ValueError("tenant_id and user_id are required")

        facts: list[CopilotFact] = []
        source_ids: dict[ContextSource, tuple[str, ...]] = {}
        for source, entity_id in entity_ids.items():
            if source not in self.providers:
                continue
            if not entity_id.strip():
                raise ValueError(f"entity id is required for {source.value}")
            source_ids[source] = (entity_id,)
            facts.extend(self.providers[source].facts(tenant_id=tenant_id, entity_id=entity_id))

        return SalesCopilotContextPackage(
            tenant_id=tenant_id,
            user_id=user_id,
            facts=tuple(facts),
            source_ids=source_ids,
        )
