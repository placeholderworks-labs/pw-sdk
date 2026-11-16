LOCALES = {
    "hindi": {"locale": "hi-IN", "script": "Devanagari", "endonym": "हिन्दी"},
    "english": {"locale": "en-IN", "script": "Latin", "endonym": "English"},
}
SUPPORTED_LANGUAGES = tuple(LOCALES)
ALIASES = {"hi": "hindi", "hindi": "hindi", "en": "english", "english": "english"}


def language_key(value: str | None, default: str = "hindi") -> str:
    key = ALIASES.get((value or "").strip().lower().split("-")[0], "")
    return key or default
