from phoenix_sales.module import MODULE_CODE, MODULE_VERSION, module_manifest


def test_sales_manifest_publishes_optional_crm_dependency():
    manifest = module_manifest()
    integration = manifest["integration"]
    dependency = integration["dependencies"][0]

    assert manifest["module"]["code"] == MODULE_CODE
    assert manifest["module"]["version"] == MODULE_VERSION
    assert dependency["module_code"] == "crm"
    assert dependency["minimum_version"] == "1.0.0"
    assert dependency["required"] is False
    assert dependency["capabilities"] == ("crm.customer_context",)


def test_sales_remains_a_sales_owned_module():
    manifest = module_manifest()
    assert manifest["module"]["required_entitlements"] == ("sales",)
    assert manifest["integration"]["provided_contracts"] == ("sales.customer_commercial.v1",)
