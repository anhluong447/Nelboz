from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List


@dataclass
class FlowAExecutionContext:
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    cards_inspected: int = 0
    comments_submitted: int = 0
    skipped_count: int = 0
    errors: List[str] = field(default_factory=list)


@dataclass
class FlowBExecutionContext:
    post_id: str = ""
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    comments_inspected: int = 0
    replies_submitted: int = 0
    errors: List[str] = field(default_factory=list)

