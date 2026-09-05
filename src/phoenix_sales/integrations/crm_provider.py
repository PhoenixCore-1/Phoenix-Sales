"""Optional runtime bridge from Sales to the CRM published capability."""

from __future__ import annotations

from phoenix_sales.api.contracts import RequestContext
from phoenix_sales.integrations.crm import CRMCustomerContext, CRMCustomerProvider


class OptionalCRMIntegration:
    """Expose CRM context to Sales when the optional capability is installed."""

    def __init__(self, provider: CRMCustomerProvider | None = None) -> None:
        self._provider = provider

    @property
    def available(self) -> bool:
        return self._provider is not None

    def customer(self, context: RequestContext, customer_id: str):
        """Return a CRM customer reference, or None when CRM is unavailable."""
        if self._provider is None:
            return None
        return self._provider.get_customer(
            tenant_id=context.tenant.tenant_id,
            customer_id=customer_id,
        )

    def customer_context(
        self,
        context: RequestContext,
        customer_id: str,
    ) -> CRMCustomerContext | None:
        """Return CRM relationship context, or None when CRM is unavailable."""
        if self._provider is None:
            return None
        return self._provider.get_customer_context(
            tenant_id=context.tenant.tenant_id,
            customer_id=customer_id,
        )

    def contacts(self, context: RequestContext, customer_id: str):
        """Return CRM contacts, or an empty tuple when CRM is unavailable."""
        if self._provider is None:
            return ()
        return self._provider.get_contacts(
            tenant_id=context.tenant.tenant_id,
            customer_id=customer_id,
        )
