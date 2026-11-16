import re
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

E164 = re.compile(r"^\+[1-9]\d{6,14}$")
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CURRENCY = re.compile(r"^[A-Z]{3}$")
URL = re.compile(r"^https?://\S+$")

AttributeValue = str | int | float | bool


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Stage(StrEnum):
    BROWSE = "browse"
    PRODUCT_VIEW = "product_view"
    CART = "cart"
    CHECKOUT = "checkout"
    PAYMENT_PENDING = "payment_pending"
    PAYMENT_FAILED = "payment_failed"


class EventKind(StrEnum):
    JOURNEY_INITIATED = "journey.initiated"
    JOURNEY_IN_PROGRESS = "journey.in_progress"
    JOURNEY_ABANDONED = "journey.abandoned"
    PAYMENT_INITIATED = "payment.initiated"
    PAYMENT_SUCCEEDED = "payment.succeeded"
    PAYMENT_FAILED = "payment.failed"
    BOOKING_CONFIRMED = "booking.confirmed"


class Consent(Strict):
    whatsapp: bool | None = None
    email: bool | None = None
    call: bool | None = None

    def allows(self, channel: str) -> bool:
        value = getattr(self, channel, None)
        return value is not False


class Fact(Strict):
    key: str = Field(min_length=1, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    label: str = Field(min_length=1, max_length=120)
    value: str = Field(max_length=1000)
    speakable: bool = True


def check_currency(value: str) -> str:
    value = value.upper()
    if not CURRENCY.match(value):
        raise ValueError("must be a 3-letter ISO 4217 code")
    return value


def check_url(value: str | None) -> str | None:
    if value is not None and not URL.match(value):
        raise ValueError("must be an http(s) URL")
    return value


class Money(Strict):
    amount: float = Field(ge=0)
    currency: str

    @field_validator("currency")
    @classmethod
    def valid_currency(cls, value: str) -> str:
        return check_currency(value)
