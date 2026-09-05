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

__all__ = [
    "CRM_CONTACT_CONTRACT",
    "CRM_CUSTOMER_CONTRACT",
    "CRM_CUSTOMER_CONTEXT_CAPABILITY",
    "CRMContactReference",
    "CRMCustomerContext",
    "CRMCustomerProvider",
    "CRMCustomerReference",
    "OptionalCRMIntegration",
]
