"""Sales adapter boundary for Phoenix platform context."""

from phoenix_sales.api.contracts import RequestContext


class SalesPlatformAdapter:
    """Expose platform context to Sales without coupling Sales to Core internals."""

    def __init__(self, context: RequestContext) -> None:
        self._context = context

    @property
    def context(self) -> RequestContext:
        """Return the immutable platform context for the current operation."""
        return self._context

    @property
    def tenant_id(self) -> str:
        return self._context.tenant.tenant_id

    @property
    def user_id(self) -> str:
        return self._context.user.user_id

    @property
    def access_scope(self):
        """Return the Core-resolved access scope for this request."""
        return self._context.access_scope

    def can_access_resource(self, resource_id: str) -> bool:
        """Check visibility using the scope resolved by Core."""
        return self._context.can_access_resource(resource_id)

    def has_permission(self, permission: str) -> bool:
        return self._context.has_permission(permission)

    def has_entitlement(self, entitlement: str) -> bool:
        return self._context.has_entitlement(entitlement)
