from phoenix_sales.api.contracts import RequestContext, TenantContext, UserContext
from phoenix_sales.integrations.crm import CRMCustomerReference
from phoenix_sales.integrations.crm_provider import OptionalCRMIntegration


class FakeCRM:
    def get_customer(self, *, tenant_id: str, customer_id: str):
        return CRMCustomerReference(tenant_id, customer_id, "Example Customer")

    def get_customer_context(self, *, tenant_id: str, customer_id: str):
        return None

    def get_contacts(self, *, tenant_id: str, customer_id: str):
        return ()


def context():
    return RequestContext(TenantContext("tenant-1"), UserContext("user-1"))


def test_sales_degrades_gracefully_when_crm_is_not_installed():
    integration = OptionalCRMIntegration()

    assert integration.available is False
    assert integration.customer(context(), "customer-1") is None
    assert integration.customer_context(context(), "customer-1") is None
    assert integration.contacts(context(), "customer-1") == ()


def test_sales_can_consume_crm_customer_capability_when_available():
    integration = OptionalCRMIntegration(FakeCRM())

    customer = integration.customer(context(), "customer-1")

    assert integration.available is True
    assert customer is not None
    assert customer.customer_id == "customer-1"
    assert customer.tenant_id == "tenant-1"
