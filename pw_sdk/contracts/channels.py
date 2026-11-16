from enum import StrEnum


class ChannelName(StrEnum):
    VOICE = "voice"
    WHATSAPP = "whatsapp"
    EMAIL = "email"


class Surface(StrEnum):
    WEBSITE = "website"
    WHATSAPP = "whatsapp"
    WEBVOICE = "webvoice"
    CALLVOICE = "callvoice"
