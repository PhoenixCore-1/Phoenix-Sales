from phoenix_sales.api.contracts import (
    EntitlementContext,
    PermissionContext,
    RequestContext,
    TenantContext,
    UserContext,
)
from phoenix_sales.integrations.platform import SalesPlatformAdapter


def test_platform_adapter_exposes_context_without_core_dependency():
    context = RequestContext(
        tenant=TenantContext("tenant-001"),
        user=UserContext("user-001"),
        permissions=PermissionContext(frozenset({"sales.opportunity.read"})),
        entitlements=EntitlementContext(frozenset({"sales"})),
        correlation_id="corr-001",
    )

    adapter = SalesPlatformAdapter(context)

    assert adapter.context is context
    assert adapter.tenant_id == "tenant-001"
    assert adapter.user_id == "user-001"
    assert adapter.has_permission("sales.opportunity.read")
    assert adapter.has_entitlement("sales")


def test_platform_adapter_preserves_denied_access():
    adapter = SalesPlatformAdapter(
        RequestContext(
            tenant=TenantContext("tenant-001"),
            user=UserContext("user-001"),
        )
    )

    assert not adapter.has_permission("sales.opportunity.write")
    assert not adapter.has_entitlement("sales")
