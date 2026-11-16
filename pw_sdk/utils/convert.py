from typing import Any

TRUE = {"1", "true", "yes", "on", "y"}
FALSE = {"0", "false", "no", "off", "n"}


def as_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return default if text.lower() in ("", "none", "null", "undefined", "nan") else text


def as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    text = as_str(value).lower()
    if text in TRUE:
        return True
    if text in FALSE:
        return False
    return default


def as_float(value: Any, default: float | None = None) -> float | None:
    if isinstance(value, bool):
        return default
    try:
        number = float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return default
    return default if number != number else number


def as_int(value: Any, default: int | None = None) -> int | None:
    number = as_float(value)
    return default if number is None else int(number)
