from dataclasses import dataclass

import pytest

from phoenix_sales.api.contracts import RequestContext, TenantContext, UserContext
from phoenix_sales.integrations.crm_runtime import OptionalCoreCRMIntegration


@dataclass
class Response:
    success: bool
    data: object = None
    error: str | None = None


class Invoker:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def invoke(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


def context():
    return RequestContext(
        tenant=TenantContext("tenant-1"),
        user=UserContext("user-1"),
        correlation_id="corr-1",
    )


def crm_payload(tenant_id="tenant-1"):
    return {
        "tenant_id": tenant_id,
        "customer": {
            "tenant_id": tenant_id,
            "customer_id": "customer-1",
            "name": "Acme",
            "status": "active",
            "customer_type": "Builder",
            "call_class": "B",
            "account_owner_id": "user-2",
        },
        "primary_contact": {
            "tenant_id": tenant_id,
            "contact_id": "contact-1",
            "customer_id": "customer-1",
            "name": "Jane",
            "email": "jane@example.test",
            "phone": "123",
            "primary": True,
        },
        "open_follow_up_count": 2,
        "potential_summary": "Fastener expansion",
    }


def test_sales_requests_crm_through_core_invocation_port():
    invoker = Invoker(Response(True, crm_payload()))
    integration = OptionalCoreCRMIntegration(invoker)

    result = integration.customer_context(context(), "customer-1")

    assert result is not None
    assert result.customer.name == "Acme"
    assert result.primary_contact.name == "Jane"
    assert result.open_follow_up_count == 2
    assert invoker.calls[0]["source_module"] == "sales"
    assert invoker.calls[0]["target_module"] == "crm"
    assert invoker.calls[0]["contract"] == "crm.customer.v1"
    assert invoker.calls[0]["operation"] == "get_customer_context"
    assert invoker.calls[0]["payload"] == {"customer_id": "customer-1"}


def test_sales_degrades_when_crm_is_not_installed():
    integration = OptionalCoreCRMIntegration()
    assert integration.available is False
    assert integration.customer_context(context(), "customer-1") is None


def test_sales_degrades_when_core_reports_unavailable_capability():
    invoker = Invoker(Response(False, error="Target module is not enabled: crm"))
    integration = OptionalCoreCRMIntegration(invoker)
    assert integration.customer_context(context(), "customer-1") is None


def test_sales_rejects_cross_tenant_crm_response():
    invoker = Invoker(Response(True, crm_payload("tenant-2")))
    integration = OptionalCoreCRMIntegration(invoker)
    with pytest.raises(PermissionError, match="tenant does not match"):
        integration.customer_context(context(), "customer-1")
