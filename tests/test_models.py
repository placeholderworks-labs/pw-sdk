import json
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from pw_sdk import CustomerRecord, EventKind, OutcomeEvent, Stage
from pw_sdk.schema import json_schemas, write_schemas


def record(**overrides):
    data = {
        "ref": {"reference_id": "C-1"},
        "customer": {"name": "Asha", "phone": "+919812345678"},
        "cart": {"currency": "inr", "total": 15400, "items": [{"item_id": "1", "type": "flight", "title": "Delhi to Goa"}]},
    }
    data.update(overrides)
    return CustomerRecord.model_validate(data)


def test_valid_record_defaults():
    rec = record()
    assert rec.schema_version == "1"
    assert rec.journey.stage is Stage.CART
    assert rec.cart.currency == "INR"
    assert rec.spoken_summary() == "Delhi to Goa"


def test_summary_wins_over_items():
    assert record(summary="Goa trip").spoken_summary() == "Goa trip"


@pytest.mark.parametrize("phone", ["9812345678", "+0123456789", "+91 98123 45678", "+12"])
def test_phone_must_be_e164(phone):
    with pytest.raises(ValidationError):
        record(customer={"name": "A", "phone": phone})


def test_customer_needs_phone_or_email():
    with pytest.raises(ValidationError):
        record(customer={"name": "A"})
    assert record(customer={"email": "A@Example.com"}).customer.email == "a@example.com"


def test_amounts_and_currency():
    with pytest.raises(ValidationError):
        record(cart={"currency": "INR", "total": -1})
    with pytest.raises(ValidationError):
        record(cart={"currency": "RUPEE", "total": 1})


def test_dates_must_be_aware_and_ordered():
    with pytest.raises(ValidationError):
        record(ref={"reference_id": "x", "occurred_at": "2026-01-01T10:00:00"})
    with pytest.raises(ValidationError):
        record(cart={"currency": "INR", "total": 1, "items": [{
            "item_id": "1", "type": "hotel", "title": "Stay",
            "starts_at": "2026-01-05T00:00:00Z", "ends_at": "2026-01-01T00:00:00Z"}]})


def test_unknown_fields_rejected():
    with pytest.raises(ValidationError):
        record(origin="DEL")


def test_resume_url_must_be_http():
    with pytest.raises(ValidationError):
        record(journey={"resume_url": "javascript:alert(1)"})


def test_outcome_event():
    event = OutcomeEvent(event_id="e1", reference_id="C-1", kind="booking.confirmed",
                         occurred_at=datetime(2026, 1, 1, tzinfo=timezone.utc), currency="inr")
    assert event.kind is EventKind.BOOKING_CONFIRMED and event.converts and event.currency == "INR"
    assert not OutcomeEvent(event_id="e2", reference_id="C-1", kind="payment.failed",
                            occurred_at=datetime(2026, 1, 1, tzinfo=timezone.utc)).converts


def test_json_schema_export(tmp_path):
    schemas = json_schemas()
    assert set(schemas) == {"customer_record.v1.json", "outcome_event.v1.json"}
    paths = write_schemas(tmp_path)
    loaded = json.loads(paths[0].read_text())
    assert "properties" in loaded
