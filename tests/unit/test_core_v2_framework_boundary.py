"""Tests for the Sales/Core V2 Framework contract boundary."""

from phoenix_framework.contracts import ModuleLifecycle

from phoenix_sales.framework import (
    SALES_CAPABILITIES,
    SALES_ENTITLEMENT,
    SALES_NAVIGATION_KEY,
    SALES_NAVIGATION_ROUTE,
    SALES_PERMISSIONS,
    framework_contracts,
)


def test_sales_contract_uses_core_authoritative_entitlement():
    module, integration, navigation = framework_contracts()

    assert module.lifecycle is ModuleLifecycle.REGISTERED
    assert module.required_entitlements == (SALES_ENTITLEMENT,)
    assert SALES_ENTITLEMENT == "sales"
    assert SALES_PERMISSIONS == ()
    assert navigation.entitlement == SALES_ENTITLEMENT


def test_sales_framework_surface_is_explicit_and_dependency_free():
    module, integration, navigation = framework_contracts()

    assert module.code == integration.module_code == navigation.module_code == "sales"
    assert module.version == integration.version == "1.0.0"
    assert integration.dependencies == ()
    assert integration.provided_capabilities == SALES_CAPABILITIES
    assert navigation.key == SALES_NAVIGATION_KEY
    assert navigation.route == SALES_NAVIGATION_ROUTE
    assert navigation.requires_authorization
