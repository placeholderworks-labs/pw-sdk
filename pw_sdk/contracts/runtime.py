from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from pw_sdk.contracts.language import LOCALES, language_key
from pw_sdk.models import CustomerRecord


class ItemView(BaseModel):
    model_config = ConfigDict(extra="ignore")
    type: str = ""
    title: str = ""
    quantity: int = 1
    total: float | None = None
    starts_at: str = ""
    attributes: dict[str, Any] = Field(default_factory=dict)


class FactView(BaseModel):
    model_config = ConfigDict(extra="ignore")
    key: str
    label: str
    value: str
    speakable: bool = True


class RuntimeContext(BaseModel):
    model_config = ConfigDict(extra="ignore")

    channel: str = ""
    call_id: str = ""
    call_ref: str = ""
    intake: str = ""

    reference_id: str = ""
    customer_name: str = ""
    phone_number: str = ""
    email: str = ""

    stage: str = ""
    cart_summary: str = ""
    cart_total: float | None = None
    cart_discount: float | None = None
    currency: str = ""
    items: list[ItemView] = Field(default_factory=list)
    resume_url: str = ""
    facts: list[FactView] = Field(default_factory=list)

    language: str = "hindi"
    tts_profile: dict[str, Any] = Field(default_factory=dict)
    max_reply_chars: int = 350
    max_reply_sentences: int = 2

    is_phone_call: bool = False
    max_call_duration_secs: int | None = None
    seconds_remaining: int | None = None
    turn_index: int = 0
    wrap_up_reason: str = ""
    capabilities: list[str] = Field(default_factory=list)

    @classmethod
    def record_fields(cls, record: CustomerRecord) -> dict[str, Any]:
        cart = record.cart
        return {
            "reference_id": record.ref.reference_id,
            "customer_name": record.customer.name,
            "phone_number": record.customer.phone or "",
            "email": record.customer.email or "",
            "stage": record.journey.stage.value,
            "cart_summary": record.spoken_summary(),
            "cart_total": cart.total if cart else None,
            "cart_discount": cart.discount if cart and cart.discount else None,
            "currency": cart.currency if cart else "",
            "items": [
                ItemView(
                    type=item.type,
                    title=item.title,
                    quantity=item.quantity,
                    total=item.total,
                    starts_at=item.starts_at.isoformat() if item.starts_at else "",
                    attributes=dict(item.attributes),
                )
                for item in (cart.items if cart else [])
            ],
            "resume_url": record.journey.resume_url or "",
            "facts": [FactView(**fact.model_dump()) for fact in record.facts],
            "language": language_key(record.customer.language),
        }

    @classmethod
    def from_record(cls, record: CustomerRecord, **extra: Any) -> "RuntimeContext":
        return cls(**{**cls.record_fields(record), **extra})

    def language_key(self) -> str:
        key = (self.language or "").strip().lower()
        return key if key in LOCALES else "hindi"

    def can(self, action: str) -> bool:
        return action in (self.capabilities or [])

    def spoken_facts(self) -> list[FactView]:
        return [fact for fact in self.facts if fact.speakable]

    def cart_view(self) -> dict[str, Any]:
        view: dict[str, Any] = {}
        if self.reference_id:
            view["reference_id"] = self.reference_id
        if self.cart_summary:
            view["summary"] = self.cart_summary
        if self.cart_total is not None:
            view["total"] = self.cart_total
            view["currency"] = self.currency
        if self.cart_discount:
            view["discount"] = self.cart_discount
        if self.stage:
            view["stage"] = self.stage
        if self.items:
            view["items"] = [item.model_dump(exclude_defaults=True) for item in self.items]
        return view
