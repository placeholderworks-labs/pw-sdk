from datetime import datetime, timezone

import pytest

from pw_sdk import Adapter, AdapterContext, CustomerRecord, NotSupported, RejectItem, SkipItem, map_batch
from pw_sdk.loader import AdapterLoadError, instantiate

CTX = AdapterContext(intake_id="demo", received_at=datetime(2026, 1, 1, tzinfo=timezone.utc))


class DemoAdapter(Adapter):
    name = "demo.cart"
    version = "1.0.0"

    def transform_records(self, payload, ctx):
        def build(raw, index):
            if raw.get("test"):
                raise SkipItem("test record")
            if raw.get("blocked"):
                raise RejectItem("customer blocked", "blocked")
            return CustomerRecord.model_validate({
                "ref": {"reference_id": raw["id"]},
                "customer": {"name": raw.get("name", ""), "phone": raw.get("phone")},
            })
        return map_batch(payload, build)


def test_batch_reports_every_index():
    payload = [
        {"id": "1", "phone": "+919812345678"},
        {"id": "2", "phone": "12345"},
        {"id": "3", "test": True},
        {"id": "4", "blocked": True, "phone": "+919812345678"},
        {"phone": "+919812345678"},
    ]
    result = DemoAdapter().transform_records(payload, CTX)
    assert result.covers(5)
    assert [i.index for i in result.items] == [0]
    assert {r.index for r in result.rejections} == {1, 3, 4}
    assert result.rejections[0].field == "customer.phone"
    assert result.skipped[0].reason == "test record"


def test_single_object_and_wrapped_lists():
    adapter = DemoAdapter()
    assert len(adapter.transform_records({"id": "1", "phone": "+919812345678"}, CTX).items) == 1
    assert len(adapter.transform_records({"records": [{"id": "1", "phone": "+919812345678"}]}, CTX).items) == 1


def test_events_not_supported_by_default():
    with pytest.raises(NotSupported):
        DemoAdapter().transform_events({}, CTX)


def test_parse_time_applies_timezone():
    moment = Adapter.parse_time("2026-03-01 10:00:00", "Asia/Kolkata")
    assert moment.utcoffset().total_seconds() == 19800
    assert Adapter.parse_time("2026-03-01T10:00:00Z").tzinfo is not None
    assert Adapter.parse_time("") is None


def test_schema_version_check():
    class Future(DemoAdapter):
        schema_version = "9"

    with pytest.raises(AdapterLoadError):
        instantiate(Future, "future")
    with pytest.raises(AdapterLoadError):
        instantiate(dict, "dict")
    assert instantiate(DemoAdapter, "demo").describe()["name"] == "demo.cart"
