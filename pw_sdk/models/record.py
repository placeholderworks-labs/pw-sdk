from typing import Literal

from pydantic import AwareDatetime, Field, field_validator, model_validator

from pw_sdk.models.common import (
    E164,
    EMAIL,
    AttributeValue,
    Consent,
    Fact,
    Stage,
    Strict,
    check_currency,
    check_url,
)


class Ref(Strict):
    reference_id: str = Field(min_length=1, max_length=128)
    occurred_at: AwareDatetime | None = None
    campaign_id: str | None = Field(default=None, max_length=128)


class Customer(Strict):
    external_id: str | None = Field(default=None, max_length=128)
    name: str = Field(default="", max_length=200)
    phone: str | None = None
    email: str | None = None
    language: str | None = Field(default=None, max_length=16)
    consent: Consent = Field(default_factory=Consent)

    @field_validator("phone")
    @classmethod
    def valid_phone(cls, value: str | None) -> str | None:
        if value is not None and not E164.match(value):
            raise ValueError("must be E.164, for example +919812345678")
        return value

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str | None) -> str | None:
        if value is not None and not EMAIL.match(value):
            raise ValueError("must be a valid email address")
        return value.lower() if value else value

    @model_validator(mode="after")
    def reachable(self):
        if not self.phone and not self.email:
            raise ValueError("customer needs a phone or an email")
        return self


class Journey(Strict):
    stage: Stage = Stage.CART
    abandoned_at: AwareDatetime | None = None
    resume_url: str | None = None

    @field_validator("resume_url")
    @classmethod
    def valid_resume_url(cls, value: str | None) -> str | None:
        return check_url(value)


class CartItem(Strict):
    item_id: str = Field(min_length=1, max_length=128)
    type: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=300)
    quantity: int = Field(default=1, ge=1)
    unit_price: float | None = Field(default=None, ge=0)
    total: float | None = Field(default=None, ge=0)
    starts_at: AwareDatetime | None = None
    ends_at: AwareDatetime | None = None
    attributes: dict[str, AttributeValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def ordered_dates(self):
        if self.starts_at and self.ends_at and self.ends_at < self.starts_at:
            raise ValueError("ends_at is before starts_at")
        return self


class Cart(Strict):
    currency: str
    total: float = Field(ge=0)
    discount: float = Field(default=0, ge=0)
    items: list[CartItem] = Field(default_factory=list, max_length=100)

    @field_validator("currency")
    @classmethod
    def valid_currency(cls, value: str) -> str:
        return check_currency(value)


class Schedule(Strict):
    scheduled_at: AwareDatetime | None = None


class CustomerRecord(Strict):
    schema_version: Literal["1"] = "1"
    ref: Ref
    customer: Customer
    journey: Journey = Field(default_factory=Journey)
    cart: Cart | None = None
    summary: str = Field(default="", max_length=500)
    facts: list[Fact] = Field(default_factory=list, max_length=50)
    schedule: Schedule = Field(default_factory=Schedule)

    def spoken_summary(self) -> str:
        if self.summary:
            return self.summary
        if not self.cart or not self.cart.items:
            return ""
        return ", ".join(item.title for item in self.cart.items[:3])
