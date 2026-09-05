from phoenix_sales.integrations.crm import (
    CRMContactReference,
    CRMCustomerContext,
    CRMCustomerReference,
    customer_context_payload,
)


def test_customer_reference_is_stable_and_transport_neutral():
    customer = CRMCustomerReference(
        tenant_id="tenant-1",
        customer_id="customer-1",
        name="Example Customer",
        status="active",
        customer_type="Contractor",
        call_class="A",
    )
    assert customer.customer_id == "customer-1"
    assert customer.tenant_id == "tenant-1"


def test_customer_context_keeps_contact_and_tenant_boundaries():
    customer = CRMCustomerReference("tenant-1", "customer-1", "Example Customer")
    contact = CRMContactReference("tenant-1", "contact-1", "customer-1", "Jane Doe")
    context = CRMCustomerContext(
        tenant_id="tenant-1",
        customer=customer,
        primary_contact=contact,
        open_follow_up_count=2,
    )

    payload = customer_context_payload(context)
    assert payload["customer_id"] == "customer-1"
    assert payload["primary_contact_id"] == "contact-1"
    assert payload["open_follow_up_count"] == 2


def test_customer_context_rejects_cross_tenant_contact():
    customer = CRMCustomerReference("tenant-1", "customer-1", "Example Customer")
    contact = CRMContactReference("tenant-2", "contact-1", "customer-1", "Jane Doe")

    try:
        CRMCustomerContext("tenant-1", customer, primary_contact=contact)
        assert False, "expected tenant mismatch"
    except ValueError as exc:
        assert "tenant" in str(exc)


def test_customer_context_rejects_contact_for_another_customer():
    customer = CRMCustomerReference("tenant-1", "customer-1", "Example Customer")
    contact = CRMContactReference("tenant-1", "contact-1", "customer-2", "Jane Doe")

    try:
        CRMCustomerContext("tenant-1", customer, primary_contact=contact)
        assert False, "expected customer mismatch"
    except ValueError as exc:
        assert "customer" in str(exc)
