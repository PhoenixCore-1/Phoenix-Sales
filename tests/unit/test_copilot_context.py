import pytest

from phoenix_sales.domain.copilot_context import ContextSource, CopilotFact, FactType
from phoenix_sales.services.copilot_context import SalesContextProvider, SalesCopilotContextAssembler


class Provider(SalesContextProvider):
    def __init__(self, facts):
        self._facts = facts

    def facts(self, *, tenant_id, entity_id):
        assert tenant_id == "t1"
        assert entity_id == "opp-1"
        return tuple(self._facts)


def test_assembler_combines_permitted_sources():
    assembler = SalesCopilotContextAssembler({
        ContextSource.OPPORTUNITY: Provider((CopilotFact(ContextSource.OPPORTUNITY, "stage", "Negotiation"),)),
        ContextSource.QUOTE: Provider((CopilotFact(ContextSource.QUOTE, "expiry", "2026-09-10"),)),
    })
    package = assembler.assemble(
        tenant_id="t1",
        user_id="u1",
        entity_ids={ContextSource.OPPORTUNITY: "opp-1", ContextSource.QUOTE: "opp-1"},
    )
    assert len(package.known()) == 2
    assert package.source_ids[ContextSource.OPPORTUNITY] == ("opp-1",)


def test_package_separates_known_missing_and_inferred():
    from phoenix_sales.domain.copilot_context import SalesCopilotContextPackage
    package = SalesCopilotContextPackage(
        "t1", "u1", (
            CopilotFact(ContextSource.OPPORTUNITY, "stage", "Qualified"),
            CopilotFact(ContextSource.OPPORTUNITY, "decision_maker", None, FactType.MISSING),
            CopilotFact(ContextSource.OPPORTUNITY, "risk", "Likely", FactType.INFERRED),
        )
    )
    assert len(package.known()) == 1
    assert len(package.missing()) == 1
    assert len(package.inferred()) == 1


def test_missing_fact_cannot_have_value():
    with pytest.raises(ValueError, match="missing facts"):
        CopilotFact(ContextSource.OPPORTUNITY, "stage", "Qualified", FactType.MISSING)


def test_unknown_sources_are_not_forwarded():
    assembler = SalesCopilotContextAssembler({})
    package = assembler.assemble(
        tenant_id="t1", user_id="u1", entity_ids={ContextSource.CUSTOMER: "cust-1"}
    )
    assert package.facts == ()
    assert package.source_ids == {}
