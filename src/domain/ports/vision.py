from abc import ABC, abstractmethod
from typing import Any, List, Optional
from src.domain.entities.geometry import BoundingBox
from src.domain.entities.comment import CommentUnit


class ICardSegmenter(ABC):
    @abstractmethod
    def segment_cards(self, feed_image: Any) -> List[BoundingBox]:
        """Segments individual post cards from the feed image using background-color scanning."""
        pass


class IAnchorDetector(ABC):
    @abstractmethod
    def detect_post_anchor(self, card_image: Any) -> Optional[BoundingBox]:
        """Detects Like-Comment-Share action bar anchor in a post card image."""
        pass

    @abstractmethod
    def detect_reply_buttons(self, thread_image: Any) -> List[BoundingBox]:
        """Detects Like-Reply buttons in comment thread."""
        pass


class ICommentGrouper(ABC):
    @abstractmethod
    def group_comments(self, thread_image: Any) -> List[CommentUnit]:
        """Detects and groups comments with their corresponding reply anchors and nested levels."""
        pass
