from phoenix_sales.api.contracts import (
    EntitlementContext,
    PermissionContext,
    RequestContext,
    TenantContext,
    UserContext,
)


def test_request_context_carries_platform_boundary_context():
    context = RequestContext(
        tenant=TenantContext("tenant-001"),
        user=UserContext("user-001"),
        permissions=PermissionContext(frozenset({"sales.opportunity.read"})),
        entitlements=EntitlementContext(frozenset({"sales"})),
        correlation_id="corr-001",
    )

    assert context.tenant.tenant_id == "tenant-001"
    assert context.user.user_id == "user-001"
    assert context.has_permission("sales.opportunity.read")
    assert context.has_entitlement("sales")
    assert context.correlation_id == "corr-001"


def test_permission_and_entitlement_checks_are_negative_by_default():
    context = RequestContext(
        tenant=TenantContext("tenant-001"),
        user=UserContext("user-001"),
    )

    assert not context.has_permission("sales.opportunity.write")
    assert not context.has_entitlement("sales")


def test_required_identity_context_cannot_be_blank():
    try:
        TenantContext(" ")
        assert False, "Expected blank tenant ID to be rejected"
    except ValueError as exc:
        assert str(exc) == "tenant_id is required"

    try:
        UserContext("")
        assert False, "Expected blank user ID to be rejected"
    except ValueError as exc:
        assert str(exc) == "user_id is required"
