from typing import Literal

from pydantic import AwareDatetime, Field, field_validator

from pw_sdk.models.common import AttributeValue, EventKind, Strict, check_currency


class OutcomeEvent(Strict):
    schema_version: Literal["1"] = "1"
    event_id: str = Field(min_length=1, max_length=128)
    reference_id: str = Field(min_length=1, max_length=128)
    kind: EventKind
    occurred_at: AwareDatetime
    booking_id: str | None = Field(default=None, max_length=128)
    transaction_id: str | None = Field(default=None, max_length=128)
    amount: float | None = Field(default=None, ge=0)
    currency: str | None = None
    attributes: dict[str, AttributeValue] = Field(default_factory=dict)

    @field_validator("currency")
    @classmethod
    def valid_currency(cls, value: str | None) -> str | None:
        return check_currency(value) if value else value

    @property
    def converts(self) -> bool:
        return self.kind in (EventKind.BOOKING_CONFIRMED, EventKind.PAYMENT_SUCCEEDED)
