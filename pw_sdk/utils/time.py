import re
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

IST = timezone(timedelta(hours=5, minutes=30), "IST")
_DURATION = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(ms|s|m|h|d)?\s*$")
_UNITS = {"ms": 0.001, "s": 1, "m": 60, "h": 3600, "d": 86400, None: 1}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def zone(name: str | None) -> ZoneInfo | timezone:
    if not name or name.upper() == "UTC":
        return timezone.utc
    return ZoneInfo(name)


def parse_duration(value: str | int | float | None, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    if isinstance(value, (int, float)):
        return float(value)
    match = _DURATION.match(str(value))
    if not match:
        raise ValueError(f"not a duration: {value!r} (use e.g. 30s, 5m, 2h, 1d)")
    return float(match.group(1)) * _UNITS[match.group(2)]


def parse_clock(value: str | None) -> time | None:
    if not value:
        return None
    hours, _, minutes = str(value).partition(":")
    return time(int(hours), int(minutes or 0))


def next_allowed(moment: datetime, start: str | None, end: str | None, tz: str | None = "Asia/Kolkata") -> datetime:
    opens, closes = parse_clock(start), parse_clock(end)
    if opens is None or closes is None or opens == closes:
        return moment
    local = moment.astimezone(zone(tz))
    now = local.time()
    inside = opens <= now < closes if opens < closes else (now >= opens or now < closes)
    if inside:
        return moment
    candidate = local.replace(hour=opens.hour, minute=opens.minute, second=0, microsecond=0)
    if candidate <= local:
        candidate += timedelta(days=1)
    return candidate.astimezone(moment.tzinfo or timezone.utc)
