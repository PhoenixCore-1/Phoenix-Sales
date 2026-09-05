from phoenix_sales.api.contracts import (
    AccessScopeContext,
    RequestContext,
    TenantContext,
    UserContext,
)
from phoenix_sales.integrations.platform import SalesPlatformAdapter


def test_request_context_defaults_to_empty_access_scope() -> None:
    context = RequestContext(
        tenant=TenantContext("tenant-1"),
        user=UserContext("user-1"),
    )

    assert context.access_scope.resource_ids == frozenset()
    assert not context.can_access_resource("customer-1")


def test_sales_consumes_core_resolved_resource_scope() -> None:
    context = RequestContext(
        tenant=TenantContext("tenant-1"),
        user=UserContext("user-1"),
        access_scope=AccessScopeContext(
            organization_ids=frozenset({"org-1"}),
            unit_ids=frozenset({"region-1", "team-1"}),
            resource_ids=frozenset({"customer-1", "customer-2"}),
        ),
    )
    adapter = SalesPlatformAdapter(context)

    assert adapter.can_access_resource("customer-1")
    assert adapter.can_access_resource("customer-2")
    assert not adapter.can_access_resource("customer-3")
    assert adapter.access_scope.unit_ids == frozenset({"region-1", "team-1"})


def test_sales_does_not_expand_scope_itself() -> None:
    context = RequestContext(
        tenant=TenantContext("tenant-1"),
        user=UserContext("user-1"),
        access_scope=AccessScopeContext(
            unit_ids=frozenset({"team-1"}),
            resource_ids=frozenset({"customer-1"}),
        ),
    )
    adapter = SalesPlatformAdapter(context)

    assert adapter.can_access_resource("customer-1")
    assert not adapter.can_access_resource("customer-2")
