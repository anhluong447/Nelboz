from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from src.domain.entities.geometry import BoundingBox


@dataclass
class CommentUnit:
    id: str
    unit_box: BoundingBox
    level: int = 1  # 1 = top-level comment, 2 = reply
    text_box: Optional[BoundingBox] = None
    reply_button_box: Optional[BoundingBox] = None
    author: str = ""
    raw_text: str = ""
    parent_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

