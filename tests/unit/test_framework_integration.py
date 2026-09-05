from phoenix_framework.contracts import ModuleLifecycle

from phoenix_sales.framework import (
    SALES_CAPABILITIES,
    SALES_CONTRACTS,
    SALES_ENTITLEMENT,
    SALES_EVENTS,
    SALES_NAVIGATION_KEY,
    SALES_NAVIGATION_ROUTE,
    SALES_PERMISSIONS,
    framework_contracts,
    integration_contract,
    module_contract,
    navigation_contract,
)


def test_sales_module_contract_is_framework_compatible():
    contract = module_contract()

    assert contract.code == "sales"
    assert contract.name == "Sales"
    assert contract.version == "1.0.0"
    assert contract.lifecycle is ModuleLifecycle.REGISTERED
    assert contract.required_permissions == SALES_PERMISSIONS
    assert contract.required_entitlements == (SALES_ENTITLEMENT,)
    assert contract.navigation_keys == (SALES_NAVIGATION_KEY,)
    assert contract.capabilities == SALES_CAPABILITIES


def test_sales_integration_contract_publishes_v1_surface():
    contract = integration_contract()

    assert contract.module_code == "sales"
    assert contract.version == "1.0.0"
    assert contract.provided_contracts == SALES_CONTRACTS
    assert contract.provided_capabilities == SALES_CAPABILITIES
    assert contract.provided_events == SALES_EVENTS
    assert contract.dependencies == ()


def test_sales_navigation_contract_is_authorization_aware():
    navigation = navigation_contract()

    assert navigation.key == SALES_NAVIGATION_KEY
    assert navigation.label == "Sales"
    assert navigation.route == SALES_NAVIGATION_ROUTE
    assert navigation.module_code == "sales"
    assert navigation.permission == SALES_PERMISSIONS[0]
    assert navigation.entitlement == SALES_ENTITLEMENT
    assert navigation.requires_authorization


def test_sales_contract_bundle_has_expected_three_contracts():
    module, integration, navigation = framework_contracts()

    assert module.code == integration.module_code == navigation.module_code == "sales"
    assert module.version == integration.version == "1.0.0"
