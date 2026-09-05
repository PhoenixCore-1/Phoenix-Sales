"""Optional CRM integration contracts for Phoenix Sales.

Sales depends only on this published contract surface. It does not import
Phoenix CRM implementation, persistence, or domain models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol

CRM_CUSTOMER_CONTRACT = "crm.customer.v1"
CRM_CONTACT_CONTRACT = "crm.contact.v1"
CRM_CUSTOMER_CONTEXT_CAPABILITY = "crm.customer_context"


@dataclass(frozen=True)
class CRMCustomerReference:
    """Stable customer identity returned by the CRM published contract."""

    tenant_id: str
    customer_id: str
    name: str
    status: str = ""
    customer_type: str = ""
    call_class: str = ""
    account_owner_id: str | None = None

    def __post_init__(self) -> None:
        for field_name, value in (("tenant_id", self.tenant_id), ("customer_id", self.customer_id), ("name", self.name)):
            if not value.strip():
                raise ValueError(f"{field_name} is required")


@dataclass(frozen=True)
class CRMContactReference:
    """Stable contact identity returned by the CRM published contract."""

    tenant_id: str
    contact_id: str
    customer_id: str
    name: str
    email: str | None = None
    phone: str | None = None
    primary: bool = False

    def __post_init__(self) -> None:
        for field_name, value in (
            ("tenant_id", self.tenant_id),
            ("contact_id", self.contact_id),
            ("customer_id", self.customer_id),
            ("name", self.name),
        ):
            if not value.strip():
                raise ValueError(f"{field_name} is required")


@dataclass(frozen=True)
class CRMCustomerContext:
    """Read-only CRM context Sales may use for customer-aware workflows."""

    tenant_id: str
    customer: CRMCustomerReference
    primary_contact: CRMContactReference | None = None
    last_interaction_at: str | None = None
    next_interaction_at: str | None = None
    open_follow_up_count: int = 0
    potential_summary: str = ""

    def __post_init__(self) -> None:
        if self.tenant_id != self.customer.tenant_id:
            raise ValueError("Customer context tenant must match customer tenant")
        if self.primary_contact is not None:
            if self.primary_contact.tenant_id != self.tenant_id:
                raise ValueError("Contact context tenant must match customer tenant")
            if self.primary_contact.customer_id != self.customer.customer_id:
                raise ValueError("Contact must belong to the customer")
        if self.open_follow_up_count < 0:
            raise ValueError("open_follow_up_count cannot be negative")


class CRMCustomerProvider(Protocol):
    """Optional provider implemented by the platform integration runtime."""

    def get_customer(self, *, tenant_id: str, customer_id: str) -> CRMCustomerReference | None: ...

    def get_customer_context(self, *, tenant_id: str, customer_id: str) -> CRMCustomerContext | None: ...

    def get_contacts(self, *, tenant_id: str, customer_id: str) -> tuple[CRMContactReference, ...]: ...


def customer_context_payload(context: CRMCustomerContext) -> Mapping[str, object]:
    """Return a transport-neutral, read-only-friendly payload for Sales."""
    return {
        "customer_id": context.customer.customer_id,
        "customer_name": context.customer.name,
        "customer_status": context.customer.status,
        "customer_type": context.customer.customer_type,
        "call_class": context.customer.call_class,
        "account_owner_id": context.customer.account_owner_id,
        "primary_contact_id": context.primary_contact.contact_id if context.primary_contact else None,
        "primary_contact_name": context.primary_contact.name if context.primary_contact else None,
        "last_interaction_at": context.last_interaction_at,
        "next_interaction_at": context.next_interaction_at,
        "open_follow_up_count": context.open_follow_up_count,
        "potential_summary": context.potential_summary,
    }
