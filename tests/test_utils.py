from datetime import datetime, timezone

import pytest

from pw_sdk.contracts.outcomes import TaskOutcome, expand
from pw_sdk.utils import auth, convert, phone
from pw_sdk.utils.time import next_allowed, parse_duration


@pytest.mark.parametrize("raw,expected", [
    ("9812345678", "+919812345678"),
    ("+91 98123 45678", "+919812345678"),
    ("919812345678", "+919812345678"),
    ("09812345678", "+919812345678"),
    ("00919812345678", "+919812345678"),
    ("+14155550100", "+14155550100"),
    ("12345", None),
    ("+9112345", None),
    ("+91981234567", None),
    ("", None),
])
def test_to_e164(raw, expected):
    assert phone.to_e164(raw) == expected


def test_national_and_helpers():
    assert phone.national("+91 98123 45678") == "9812345678"
    assert phone.national("0919812345678") == "9812345678"
    assert phone.is_indian_mobile("+919812345678") and not phone.is_indian_mobile("+914412345678")
    assert phone.msisdn("9812345678") == "919812345678"
    assert phone.country_of("+971501234567") == "AE"
    assert phone.mask("9812345678").endswith("5678")


def test_auth_helpers():
    assert auth.bearer("Bearer abc ") == "abc"
    assert auth.bearer("abc") == "abc"
    assert auth.authorization_value("abc") == "Bearer abc"
    assert auth.authorization_value("Token abc") == "Token abc"
    assert auth.same_secret("x", "x") and not auth.same_secret("x", "y") and not auth.same_secret("", "")


def test_converters():
    assert convert.as_bool("Yes") and not convert.as_bool("off") and convert.as_bool("?", True)
    assert convert.as_float("1,200.5") == 1200.5 and convert.as_float("nan") is None
    assert convert.as_int("3.9") == 3 and convert.as_str(" null ") == ""


def test_durations():
    assert parse_duration("30m") == 1800 and parse_duration("2h") == 7200 and parse_duration(5) == 5.0
    with pytest.raises(ValueError):
        parse_duration("soon")


def test_next_allowed_window():
    inside = datetime(2026, 1, 1, 6, 0, tzinfo=timezone.utc)
    assert next_allowed(inside, "09:00", "21:00") == inside
    late = datetime(2026, 1, 1, 17, 0, tzinfo=timezone.utc)
    moved = next_allowed(late, "09:00", "21:00")
    assert moved > late and moved.astimezone(timezone.utc).hour == 3 and moved.minute == 30
    assert next_allowed(late, None, None) == late


def test_outcome_groups():
    assert TaskOutcome.ANSWERED in expand(["success"])
    assert expand(["no_answer", "failed"]) == {TaskOutcome.NO_ANSWER, TaskOutcome.FAILED}
    assert len(expand(None)) == len(TaskOutcome)
