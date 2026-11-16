SCHEMA_VERSION = "1"
SUPPORTED_SCHEMA_VERSIONS = ("1",)
SDK_VERSION = "0.1.0"


def is_supported(schema_version: str) -> bool:
    return schema_version in SUPPORTED_SCHEMA_VERSIONS
