from phoenix_sales.module import MODULE_CODE, MODULE_NAME, MODULE_VERSION, module_metadata


def test_module_identity():
    assert MODULE_CODE == "sales"
    assert MODULE_NAME == "Sales"
    assert MODULE_VERSION == "1.0.0"


def test_module_metadata():
    assert module_metadata() == {
        "code": "sales",
        "name": "Sales",
        "version": "1.0.0",
    }
