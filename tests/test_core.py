import os
from datetime import datetime, timezone

import pytest

from pw_sdk import config
from pw_sdk.contracts.runtime import RuntimeContext
from pw_sdk.registry import ProviderRegistry, UnknownProvider
from pw_sdk import CustomerRecord


def test_registry_register_lazy_and_unknown():
    registry: ProviderRegistry = ProviderRegistry("thing")

    @registry.register("one")
    class One:
        def __init__(self, value=1):
            self.value = value

    registry.add("lazy", "collections:OrderedDict")
    assert registry.create("one", 5).value == 5
    assert registry.get("lazy").__name__ == "OrderedDict"
    assert "one" in registry and registry.names() == ["lazy", "one"]
    with pytest.raises(UnknownProvider):
        registry.get("missing")


def test_client_config_load_and_env(tmp_path, monkeypatch):
    (tmp_path / "pw.toml").write_text(
        '[client]\nslug = "demo"\n[voice]\nstt = "deepgram"\n'
        '[intakes.demo_cart]\nadapter = "demo.cart"\njourney = "cart"\n[env]\nLOG_LEVEL = "DEBUG"\n'
    )
    (tmp_path / ".env").write_text("PW_TEST_SECRET=abc\n")
    monkeypatch.delenv("PW_CONFIG", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.delenv("STT_PROVIDER", raising=False)
    cfg = config.load(tmp_path / "pw.toml")
    assert cfg.client.slug == "demo" and cfg.intakes["demo_cart"].adapter == "demo.cart"
    assert cfg.get("voice.stt") == "deepgram" and cfg.get("voice.missing", 1) == 1
    assert os.environ["PW_TEST_SECRET"] == "abc"
    applied = config.apply_env(cfg, {"STT_PROVIDER": "voice.stt"})
    assert applied == {"LOG_LEVEL": "DEBUG", "STT_PROVIDER": "deepgram"}
    monkeypatch.delenv("PW_TEST_SECRET", raising=False)


def test_runtime_context_from_record():
    record = CustomerRecord.model_validate({
        "ref": {"reference_id": "C-9"},
        "customer": {"name": "Ravi", "phone": "+919812345678", "language": "en"},
        "journey": {"stage": "payment_failed", "resume_url": "https://example.com/r/1"},
        "cart": {"currency": "INR", "total": 8200, "discount": 200, "items": [
            {"item_id": "f1", "type": "flight", "title": "Delhi to Goa", "starts_at": "2026-12-01T06:00:00+05:30",
             "attributes": {"pnr": "AB12"}}]},
        "facts": [{"key": "tier", "label": "Tier", "value": "Gold", "speakable": False}],
    })
    ctx = RuntimeContext.from_record(record, channel="acefone", is_phone_call=True, capabilities=["end_call"])
    assert ctx.language_key() == "english" and ctx.cart_summary == "Delhi to Goa"
    assert ctx.can("end_call") and not ctx.can("transfer_to_agent")
    assert ctx.cart_view()["items"][0]["attributes"] == {"pnr": "AB12"}
    assert ctx.spoken_facts() == []
    again = RuntimeContext.model_validate(ctx.model_dump())
    assert again == ctx
