from collections.abc import Callable
from importlib import import_module
from importlib.metadata import entry_points
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class UnknownProvider(LookupError):
    pass


class ProviderRegistry(Generic[T]):
    def __init__(self, kind: str, group: str | None = None):
        self.kind = kind
        self.group = group
        self._items: dict[str, type[T] | Callable[..., T] | str] = {}
        self._loaded_entry_points = False

    def register(self, name: str) -> Callable[[type[T]], type[T]]:
        def decorate(cls: type[T]) -> type[T]:
            self._items[name] = cls
            return cls

        return decorate

    def add(self, name: str, target: type[T] | Callable[..., T] | str) -> None:
        self._items[name] = target

    def _load_entry_points(self) -> None:
        if self._loaded_entry_points or not self.group:
            return
        self._loaded_entry_points = True
        for point in entry_points(group=self.group):
            self._items.setdefault(point.name, point.value)

    def names(self) -> list[str]:
        self._load_entry_points()
        return sorted(self._items)

    def __contains__(self, name: str) -> bool:
        self._load_entry_points()
        return name in self._items

    def get(self, name: str) -> type[T] | Callable[..., T]:
        self._load_entry_points()
        target = self._items.get(name)
        if target is None:
            raise UnknownProvider(f"unknown {self.kind} provider {name!r}; available: {', '.join(self.names()) or 'none'}")
        if isinstance(target, str):
            module, _, attr = target.partition(":")
            target = getattr(import_module(module), attr)
            self._items[name] = target
        return target

    def create(self, name: str, *args: Any, **kwargs: Any) -> T:
        return self.get(name)(*args, **kwargs)
