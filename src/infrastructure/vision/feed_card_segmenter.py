from typing import Any, List
import numpy as np
from src.domain.entities.geometry import BoundingBox
from src.domain.ports.vision import ICardSegmenter


class FeedCardSegmenter(ICardSegmenter):
    """Segments individual post cards by analyzing background color transitions along the vertical axis of the feed."""

    def __init__(self, min_card_height: int = 180):
        self.min_card_height = min_card_height

    def segment_cards(self, feed_image: Any) -> List[BoundingBox]:
        if feed_image is None or not isinstance(feed_image, np.ndarray):
            return []

        h, w, _ = feed_image.shape
        if h < self.min_card_height:
            return []

        # Sample vertical column slice along feed center
        center_x = w // 2
        col_sample = feed_image[:, max(0, center_x - 30) : min(w, center_x + 30)]

        # Skeleton fallback: return single full viewport box if segmentation not yet calibrated
        # Actual Phase 1 algorithm will populate transitions here
        return [BoundingBox(x=0, y=0, width=w, height=h)]
