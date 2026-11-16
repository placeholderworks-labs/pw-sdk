from enum import StrEnum


class TaskOutcome(StrEnum):
    SENT = "sent"
    DELIVERED = "delivered"
    ANSWERED = "answered"
    NO_ANSWER = "no_answer"
    BUSY = "busy"
    FAILED = "failed"
    REPLIED = "replied"
    CLICKED = "clicked"
    NO_RESPONSE = "no_response"
    TRANSFERRED = "transferred"
    NOT_INTERESTED = "not_interested"
    CALLBACK = "callback"
    SKIPPED = "skipped"


SUCCESS = frozenset({TaskOutcome.SENT, TaskOutcome.DELIVERED, TaskOutcome.ANSWERED, TaskOutcome.REPLIED,
                     TaskOutcome.CLICKED, TaskOutcome.TRANSFERRED})
FAILURE = frozenset({TaskOutcome.NO_ANSWER, TaskOutcome.BUSY, TaskOutcome.FAILED, TaskOutcome.NO_RESPONSE,
                     TaskOutcome.SKIPPED})
GROUPS = {"success": SUCCESS, "failure": FAILURE, "any": frozenset(TaskOutcome)}


def expand(names: list[str] | tuple[str, ...] | None) -> frozenset[TaskOutcome]:
    if not names:
        return GROUPS["any"]
    result: set[TaskOutcome] = set()
    for name in names:
        result |= GROUPS[name] if name in GROUPS else {TaskOutcome(name)}
    return frozenset(result)
