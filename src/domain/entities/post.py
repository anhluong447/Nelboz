from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from src.domain.entities.geometry import BoundingBox


@dataclass
class PostCard:
    id: str
    card_box: BoundingBox
    text_box: Optional[BoundingBox] = None
    anchor_box: Optional[BoundingBox] = None
    comment_box: Optional[BoundingBox] = None
    raw_text: str = ""
    author: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

