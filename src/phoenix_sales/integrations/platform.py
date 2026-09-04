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

    def has_permission(self, permission: str) -> bool:
        return self._context.has_permission(permission)

    def has_entitlement(self, entitlement: str) -> bool:
        return self._context.has_entitlement(entitlement)
