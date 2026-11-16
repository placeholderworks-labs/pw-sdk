from abc import ABC
from collections.abc import Callable
from datetime import datetime
from typing import Any, ClassVar, Generic, TypeVar

from pydantic import AwareDatetime, BaseModel, Field, ValidationError

from pw_sdk.models import CustomerRecord, OutcomeEvent
from pw_sdk.version import SCHEMA_VERSION

T = TypeVar("T", CustomerRecord, OutcomeEvent)


class NotSupported(Exception):
    pass


class SkipItem(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class RejectItem(Exception):
    def __init__(self, error: str, field: str | None = None):
        super().__init__(error)
        self.error = error
        self.field = field


class AdapterContext(BaseModel):
    intake_id: str
    received_at: AwareDatetime
    timezone: str = "UTC"
    config: dict[str, Any] = Field(default_factory=dict)


class Rejection(BaseModel):
    index: int
    field: str | None = None
    error: str


class Skipped(BaseModel):
    index: int
    reason: str


class Transformed(BaseModel, Generic[T]):
    index: int
    value: T


class TransformResult(BaseModel, Generic[T]):
    items: list[Transformed[T]] = Field(default_factory=list)
    rejections: list[Rejection] = Field(default_factory=list)
    skipped: list[Skipped] = Field(default_factory=list)

    def values(self) -> list[T]:
        return [item.value for item in self.items]

    def reported(self) -> set[int]:
        return {i.index for i in self.items} | {r.index for r in self.rejections} | {s.index for s in self.skipped}

    def covers(self, count: int) -> bool:
        return self.reported() == set(range(count))


def as_batch(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("records", "events", "items", "data"):
            if isinstance(payload.get(key), list):
                return payload[key]
        return [payload]
    raise RejectItem("payload must be a JSON object or array")


def field_of(error: ValidationError) -> tuple[str | None, str]:
    first = error.errors()[0]
    loc = ".".join(str(part) for part in first.get("loc", ())) or None
    return loc, first.get("msg", str(error))


def map_batch(payload: Any, build: Callable[[Any, int], T]) -> TransformResult[T]:
    result: TransformResult[T] = TransformResult()
    for index, raw in enumerate(as_batch(payload)):
        try:
            result.items.append(Transformed(index=index, value=build(raw, index)))
        except SkipItem as skip:
            result.skipped.append(Skipped(index=index, reason=skip.reason))
        except RejectItem as reject:
            result.rejections.append(Rejection(index=index, field=reject.field, error=reject.error))
        except ValidationError as invalid:
            loc, message = field_of(invalid)
            result.rejections.append(Rejection(index=index, field=loc, error=message))
        except (KeyError, TypeError, ValueError) as broken:
            result.rejections.append(Rejection(index=index, field=None, error=f"{type(broken).__name__}: {broken}"))
    return result


class Adapter(ABC):
    name: ClassVar[str]
    version: ClassVar[str]
    schema_version: ClassVar[str] = SCHEMA_VERSION

    def transform_records(self, payload: Any, ctx: AdapterContext) -> TransformResult[CustomerRecord]:
        raise NotSupported(f"{self.name} does not accept customer records")

    def transform_events(self, payload: Any, ctx: AdapterContext) -> TransformResult[OutcomeEvent]:
        raise NotSupported(f"{self.name} does not accept outcome events")

    def describe(self) -> dict[str, str]:
        return {"name": self.name, "version": self.version, "schema_version": self.schema_version}

    @staticmethod
    def parse_time(value: Any, tz: str = "UTC") -> datetime | None:
        if value in (None, ""):
            return None
        from zoneinfo import ZoneInfo

        moment = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return moment if moment.tzinfo else moment.replace(tzinfo=ZoneInfo(tz))
