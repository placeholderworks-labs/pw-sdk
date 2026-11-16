from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class VoiceActionType(StrEnum):
    TRANSFER_TO_AGENT = "transfer_to_agent"
    END_CALL = "end_call"
    SWITCH_LANGUAGE = "switch_language"
    LOG_DISPOSITION = "log_disposition"
    SEND_BOOKING_LINK = "send_booking_link"


class DispositionOutcome(StrEnum):
    COMPLETED_BOOKING = "completed_booking"
    WILL_COMPLETE_LATER = "will_complete_later"
    NOT_INTERESTED = "not_interested"
    REQUESTED_CALLBACK = "requested_callback"
    DO_NOT_CALL = "do_not_call"
    NO_ANSWER_CONTEXT = "no_answer_context"
    OTHER = "other"


VOICE_ACTION_TYPES = tuple(item.value for item in VoiceActionType)
DISPOSITION_OUTCOMES = tuple(item.value for item in DispositionOutcome)


class VoiceAction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    action_id: str = ""
    type: str
    params: dict[str, Any] = Field(default_factory=dict)
    execute_after_speech: bool = True
    turn_id: str = ""


class ActionAck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    action_id: str = ""
    type: str = ""
    status: Literal["executed", "dropped", "failed"] = "executed"
    detail: str | None = None


class TurnMeta(BaseModel):
    model_config = ConfigDict(extra="ignore")
    turn_id: str = ""
    turn_kind: Literal["user", "greeting", "reprompt", "wrap_up", "closing", "recovery", "hold"] = "user"
    turn_reason: str | None = None
    assistant_prefix: str | None = None
    already_said: list[str] = Field(default_factory=list)
    barge_in_count: int = 0
    client_deadline_ms: int | None = None
    last_action_ack: ActionAck | None = None
