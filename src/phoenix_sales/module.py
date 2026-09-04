"""Phoenix Sales module identity and registration contract placeholder."""

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
