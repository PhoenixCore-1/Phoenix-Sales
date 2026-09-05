"""Phoenix Sales module identity and registration contract."""

MODULE_CODE = "sales"
MODULE_NAME = "Sales"
MODULE_VERSION = "1.0.0"


def module_metadata() -> dict[str, str]:
    """Return stable module metadata for Core integration."""
    return {
        "code": MODULE_CODE,
        "name": MODULE_NAME,
        "version": MODULE_VERSION,
    }


def module_manifest() -> dict[str, object]:
    """Return the published module manifest consumed by Phoenix Core."""
    return {
        "module": {
            "code": MODULE_CODE,
            "name": MODULE_NAME,
            "version": MODULE_VERSION,
            "description": "Phoenix Sales V1.0",
            "required_permissions": ("sales.view",),
            "required_entitlements": ("sales",),
            "navigation_keys": ("sales.workspace",),
            "capabilities": ("sales.customer_commercial_context",),
        },
        "integration": {
            "module_code": MODULE_CODE,
            "version": MODULE_VERSION,
            "provided_contracts": ("sales.customer_commercial.v1",),
            "provided_capabilities": ("sales.customer_commercial_context",),
            "dependencies": (
                {
                    "module_code": "crm",
                    "minimum_version": "1.0.0",
                    "required": False,
                    "capabilities": ("crm.customer_context",),
                },
            ),
        },
        "navigation": (
            {
                "key": "sales.workspace",
                "label": "Sales",
                "route": "/modules/sales",
                "module_code": MODULE_CODE,
                "permission": "sales.view",
                "entitlement": "sales",
            },
        ),
    }
