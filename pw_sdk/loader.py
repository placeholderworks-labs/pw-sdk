from importlib import import_module
from importlib.metadata import entry_points

from pw_sdk.adapter import Adapter
from pw_sdk.version import is_supported

GROUP = "pw.adapters"


class AdapterLoadError(Exception):
    pass


def discover() -> dict[str, type[Adapter]]:
    found: dict[str, type[Adapter]] = {}
    for point in entry_points(group=GROUP):
        found[point.name] = point.load()
    return found


def load(spec: str) -> Adapter:
    if ":" in spec:
        module, _, attr = spec.partition(":")
        cls = getattr(import_module(module), attr)
    else:
        available = discover()
        if spec not in available:
            raise AdapterLoadError(f"adapter {spec!r} not found; installed: {sorted(available) or 'none'}")
        cls = available[spec]
    return instantiate(cls, spec)


def instantiate(cls: type, spec: str) -> Adapter:
    if not (isinstance(cls, type) and issubclass(cls, Adapter)):
        raise AdapterLoadError(f"{spec} is not a pw_sdk Adapter")
    if not is_supported(cls.schema_version):
        raise AdapterLoadError(f"{spec} targets schema_version {cls.schema_version}, which this SDK does not support")
    return cls()
