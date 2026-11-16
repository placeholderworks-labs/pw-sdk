from typing import Any

from pydantic import BaseModel

from pw_sdk.contracts.runtime import RuntimeContext
from pw_sdk.contracts.voice import TurnMeta


class VoiceChatRequest(BaseModel):
    session_id: str
    message: str = ""
    user_type: str
    provider: str | None = None
    llm_name: str | None = None
    token: str | None = None
    is_logged_in: bool = False
    voice_context: RuntimeContext | None = None
    turn: TurnMeta | None = None


class VoiceServiceResponse(BaseModel):
    text: str = ""
    html: str | None = None
    result_id: str | None = None
    handoffToMainMenu: bool = False
    handoffToCustomerAgent: bool = False
    whatsapp_response: dict[str, Any] | None = None
    voice_action: dict[str, Any] | None = None
    voice_diagnostics: dict[str, Any] | None = None


class VoiceChatResponse(BaseModel):
    session_id: str
    response_text: str
    response_html: str | None = None
    result_id: str | None = None
    handoffToMainMenu: bool = False
    handoffToCustomerAgent: bool = False
    whatsapp_response: dict[str, Any] | None = None
    voice_action: dict[str, Any] | None = None
    voice_diagnostics: dict[str, Any] | None = None


class VoiceGreetingRequest(BaseModel):
    session_id: str
    user_type: str
    voice_context: RuntimeContext | None = None


class VoiceGreetingResponse(BaseModel):
    session_id: str
    greeting_text: str
    language: str
    already_greeted: bool = False
