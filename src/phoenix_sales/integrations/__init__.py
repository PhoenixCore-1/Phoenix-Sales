"""Published integration boundaries for Phoenix Sales."""

from phoenix_sales.integrations.crm import (
    CRM_CONTACT_CONTRACT,
    CRM_CUSTOMER_CONTRACT,
    CRM_CUSTOMER_CONTEXT_CAPABILITY,
    CRMContactReference,
    CRMCustomerContext,
    CRMCustomerProvider,
    CRMCustomerReference,
)
from phoenix_sales.integrations.crm_provider import OptionalCRMIntegration
from phoenix_sales.integrations.crm_runtime import (
    CoreInvocationPort,
    OptionalCoreCRMIntegration,
)

__all__ = [
    "CRM_CONTACT_CONTRACT",
    "CRM_CUSTOMER_CONTRACT",
    "CRM_CUSTOMER_CONTEXT_CAPABILITY",
    "CRMContactReference",
    "CRMCustomerContext",
    "CRMCustomerProvider",
    "CRMCustomerReference",
    "OptionalCRMIntegration",
    "CoreInvocationPort",
    "OptionalCoreCRMIntegration",
]
