from phoenix_framework.modules.registry import ModuleRegistry
from phoenix_framework.navigation.registry import NavigationRegistry
from phoenix_framework.registration import ModuleRegistrationBundle, register_module

from phoenix_sales.framework import framework_contracts


def test_sales_registers_through_core_v2_framework_boundary():
    module, integration, navigation = framework_contracts()
    modules = ModuleRegistry()
    navigation_registry = NavigationRegistry()

    register_module(
        ModuleRegistrationBundle(
            module=module,
            integration=integration,
            navigation=(navigation,),
        ),
        modules,
        navigation_registry,
    )

    registered = modules.get("sales")
    registered_navigation = navigation_registry.get("sales.workspace")

    assert registered.version == "1.0.0"
    assert registered.required_entitlements == ("sales",)
    assert registered.capabilities == module.capabilities
    assert registered_navigation.module_code == "sales"
    assert registered_navigation.entitlement == "sales"
    assert registered_navigation.requires_authorization
