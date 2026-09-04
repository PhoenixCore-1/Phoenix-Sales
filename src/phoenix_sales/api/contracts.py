"""Platform-facing contracts for Phoenix Sales V1.0.

These contracts define the information Sales expects from the Phoenix platform
boundary without importing Core implementation details.
"""

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class TenantContext:
    """Identifies the tenant within which a Sales operation is executed."""

    tenant_id: str

    def __post_init__(self) -> None:
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")


@dataclass(frozen=True)
class UserContext:
    """Identifies the authenticated platform user."""

    user_id: str

    def __post_init__(self) -> None:
        if not self.user_id.strip():
            raise ValueError("user_id is required")


@dataclass(frozen=True)
class PermissionContext:
    """Effective permissions available to the current user."""

    permissions: frozenset[str] = field(default_factory=frozenset)

    def has(self, permission: str) -> bool:
        return permission in self.permissions


@dataclass(frozen=True)
class EntitlementContext:
    """Module/licensing entitlements granted to the current tenant."""

    entitlements: frozenset[str] = field(default_factory=frozenset)

    def enabled(self, entitlement: str) -> bool:
        return entitlement in self.entitlements


@dataclass(frozen=True)
class RequestContext:
    """Security and trace context propagated across the module boundary."""

    tenant: TenantContext
    user: UserContext
    permissions: PermissionContext = field(default_factory=PermissionContext)
    entitlements: EntitlementContext = field(default_factory=EntitlementContext)
    correlation_id: str = ""
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.correlation_id and not self.correlation_id.strip():
            raise ValueError("correlation_id must not be blank")

    def has_permission(self, permission: str) -> bool:
        return self.permissions.has(permission)

    def has_entitlement(self, entitlement: str) -> bool:
        return self.entitlements.enabled(entitlement)
