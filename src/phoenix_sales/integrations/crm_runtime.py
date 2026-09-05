"""Sales adapter for the Core-routed CRM published capability."""

from __future__ import annotations

from typing import Mapping, Protocol

from phoenix_sales.api.contracts import RequestContext
from phoenix_sales.integrations.crm import (
    CRM_CUSTOMER_CONTEXT_CAPABILITY,
    CRM_CUSTOMER_CONTRACT,
    CRMCustomerContext,
    CRMCustomerReference,
    CRMContactReference,
)


class InvocationResult(Protocol):
    success: bool
    data: object
    error: str | None


class CoreInvocationPort(Protocol):
    """Transport-neutral port implemented by the Phoenix host/Core adapter."""

    def invoke(
        self,
        *,
        source_module: str,
        target_module: str,
        contract: str,
        operation: str,
        context: RequestContext,
        payload: Mapping[str, object] | None = None,
    ) -> InvocationResult:
        ...


class OptionalCoreCRMIntegration:
    """Consume CRM only through the Core invocation boundary."""

    def __init__(self, invoker: CoreInvocationPort | None = None) -> None:
        self._invoker = invoker

    @property
    def available(self) -> bool:
        return self._invoker is not None

    def customer_context(
        self,
        context: RequestContext,
        customer_id: str,
    ) -> CRMCustomerContext | None:
        if self._invoker is None:
            return None

        response = self._invoker.invoke(
            source_module="sales",
            target_module="crm",
            contract=CRM_CUSTOMER_CONTRACT,
            operation="get_customer_context",
            context=context,
            payload={"customer_id": customer_id},
        )
        if not response.success or response.data is None:
            return None
        return self._to_context(response.data, context.tenant.tenant_id)

    @staticmethod
    def _to_context(value: object, tenant_id: str) -> CRMCustomerContext:
        if not isinstance(value, Mapping):
            raise ValueError("CRM customer context response must be a mapping")

        response_tenant_id = str(value.get("tenant_id", "")).strip()
        if response_tenant_id != tenant_id:
            raise PermissionError("CRM customer context tenant does not match Sales request tenant")

        customer = value.get("customer")
        if not isinstance(customer, Mapping):
            raise ValueError("CRM customer context is missing customer")

        customer_tenant_id = str(customer.get("tenant_id", "")).strip()
        if customer_tenant_id != tenant_id:
            raise PermissionError("CRM customer tenant does not match Sales request tenant")

        reference = CRMCustomerReference(
            tenant_id=customer_tenant_id,
            customer_id=str(customer.get("customer_id", "")),
            name=str(customer.get("name", "")),
            status=str(customer.get("status", "")),
            customer_type=str(customer.get("customer_type", "")),
            call_class=str(customer.get("call_class", "")),
            account_owner_id=(
                str(customer["account_owner_id"])
                if customer.get("account_owner_id") is not None
                else None
            ),
        )

        contact_value = value.get("primary_contact")
        contact = None
        if isinstance(contact_value, Mapping):
            contact_tenant_id = str(contact_value.get("tenant_id", "")).strip()
            if contact_tenant_id != tenant_id:
                raise PermissionError("CRM contact tenant does not match Sales request tenant")
            contact = CRMContactReference(
                tenant_id=contact_tenant_id,
                contact_id=str(contact_value.get("contact_id", "")),
                customer_id=str(contact_value.get("customer_id", reference.customer_id)),
                name=str(contact_value.get("name", "")),
                email=contact_value.get("email"),
                phone=contact_value.get("phone"),
                primary=bool(contact_value.get("primary", False)),
            )

        return CRMCustomerContext(
            tenant_id=tenant_id,
            customer=reference,
            primary_contact=contact,
            last_interaction_at=value.get("last_interaction_at"),
            next_interaction_at=value.get("next_interaction_at"),
            open_follow_up_count=int(value.get("open_follow_up_count", 0)),
            potential_summary=str(value.get("potential_summary", "")),
        )


__all__ = ["CoreInvocationPort", "OptionalCoreCRMIntegration", "CRM_CUSTOMER_CONTEXT_CAPABILITY"]
