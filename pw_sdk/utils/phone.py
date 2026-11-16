import re

_NON_DIGIT = re.compile(r"\D")

CALLING_CODES = {
    "IN": "91",
    "US": "1",
    "CA": "1",
    "GB": "44",
    "AE": "971",
    "SA": "966",
    "SG": "65",
    "AU": "61",
    "NP": "977",
    "BD": "880",
    "LK": "94",
}
NATIONAL_LENGTH = {"IN": 10, "US": 10, "CA": 10, "GB": 10, "AE": 9, "SA": 9, "SG": 8, "AU": 9}


def digits(raw: str | None) -> str:
    return _NON_DIGIT.sub("", raw or "")


def last10(raw: str | None) -> str:
    return digits(raw)[-10:]


def national(raw: str | None, country: str = "IN") -> str:
    number = digits(raw)
    code = CALLING_CODES.get(country, "")
    length = NATIONAL_LENGTH.get(country, 10)
    while len(number) > length:
        if code and number.startswith(code):
            number = number[len(code):]
        elif number.startswith("0"):
            number = number[1:]
        else:
            break
    return number[-length:] if len(number) > length else number


def to_e164(raw: str | None, default_country: str = "IN") -> str | None:
    text = (raw or "").strip()
    number = digits(text)
    if not number:
        return None
    if text.startswith("+") or text.startswith("00"):
        number = number[2:] if text.startswith("00") else number
        if not 7 <= len(number) <= 15 or number[0] == "0":
            return None
        country = country_of(number)
        expected = NATIONAL_LENGTH.get(country or "")
        if expected and len(number) - len(CALLING_CODES[country]) != expected:
            return None
        return f"+{number}"
    code = CALLING_CODES.get(default_country)
    if not code:
        return None
    length = NATIONAL_LENGTH.get(default_country, 10)
    if len(number) == length + len(code) and number.startswith(code):
        return f"+{number}"
    local = national(number, default_country)
    if len(local) != length:
        return None
    return f"+{code}{local}"


def country_of(e164: str) -> str | None:
    number = digits(e164)
    for country, code in sorted(CALLING_CODES.items(), key=lambda kv: -len(kv[1])):
        if number.startswith(code):
            return country
    return None


def is_indian_mobile(raw: str | None) -> bool:
    number = national(raw, "IN")
    return len(number) == 10 and number[0] in "6789"


def msisdn(raw: str | None, default_country: str = "IN") -> str:
    e164 = to_e164(raw, default_country)
    return e164[1:] if e164 else digits(raw)


def mask(raw: str | None) -> str:
    number = digits(raw)
    return number if len(number) <= 4 else "•" * (len(number) - 4) + number[-4:]
