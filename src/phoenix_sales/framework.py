"""Phoenix Generic Framework integration for the Sales module.

This adapter is intentionally limited to Framework-facing contracts. Phoenix
Core remains authoritative for identity, tenancy, permissions, entitlements,
security, licensing and module lifecycle authority.
"""

from phoenix_framework.contracts import (
    ModuleContract,
    ModuleIntegrationContract,
    NavigationContract,
)
from phoenix_framework.contracts.module import ModuleLifecycle

from phoenix_sales.module import MODULE_CODE, MODULE_NAME, MODULE_VERSION


SALES_NAVIGATION_KEY = "sales.workspace"
SALES_NAVIGATION_ROUTE = "/modules/sales"
SALES_ENTITLEMENT = "sales"

SALES_PERMISSIONS = ()

SALES_CAPABILITIES = (
    "sales.opportunities",
    "sales.solutions",
    "sales.pricing",
    "sales.quotes",
    "sales.orders",
    "sales.forecasting",
    "sales.commissions",
    "sales.competitor_pricing",
    "sales.ai",
)

SALES_CONTRACTS = (
    "sales.opportunity.v1",
    "sales.solution.v1",
    "sales.quote.v1",
    "sales.order.v1",
)

SALES_EVENTS = (
    "sales.opportunity.created.v1",
    "sales.opportunity.updated.v1",
    "sales.quote.sent.v1",
    "sales.quote.accepted.v1",
    "sales.order.confirmed.v1",
    "sales.order.fulfilled.v1",
)


def module_contract() -> ModuleContract:
    """Return the Framework discovery contract for Sales."""
    return ModuleContract(
        code=MODULE_CODE,
        name=MODULE_NAME,
        version=MODULE_VERSION,
        lifecycle=ModuleLifecycle.REGISTERED,
        description="Phoenix Sales V1.0 business application.",
        required_permissions=SALES_PERMISSIONS,
        required_entitlements=(SALES_ENTITLEMENT,),
        navigation_keys=(SALES_NAVIGATION_KEY,),
        capabilities=SALES_CAPABILITIES,
        metadata={"product": "Phoenix Sales", "api_version": "v1"},
    )


def integration_contract() -> ModuleIntegrationContract:
    """Return the published Sales integration surface."""
    return ModuleIntegrationContract(
        module_code=MODULE_CODE,
        version=MODULE_VERSION,
        provided_contracts=SALES_CONTRACTS,
        provided_capabilities=SALES_CAPABILITIES,
        provided_events=SALES_EVENTS,
        dependencies=(),
        metadata={"product": "Phoenix Sales", "api_version": "v1"},
    )


def navigation_contract() -> NavigationContract:
    """Return the Sales workspace contribution to Platform navigation."""
    return NavigationContract(
        key=SALES_NAVIGATION_KEY,
        label=MODULE_NAME,
        route=SALES_NAVIGATION_ROUTE,
        module_code=MODULE_CODE,
        icon="sales",
        entitlement=SALES_ENTITLEMENT,
        order=30,
    )


def framework_contracts() -> tuple[ModuleContract, ModuleIntegrationContract, NavigationContract]:
    """Return all Framework-facing Sales contracts in registration order."""
    return module_contract(), integration_contract(), navigation_contract()
