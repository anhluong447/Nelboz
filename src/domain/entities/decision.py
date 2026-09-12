from dataclasses import dataclass
from enum import Enum


class ActionType(str, Enum):
    COMMENT = "comment"
    REPLY = "reply"
    SKIP = "skip"


@dataclass(frozen=True)
class ActionDecision:
    should_act: bool
    text: str = ""
    action_type: ActionType = ActionType.SKIP
    reason: str = ""
    confidence: float = 1.0
