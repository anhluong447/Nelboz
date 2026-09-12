from typing import Any, List, Optional
import numpy as np
from src.domain.entities.geometry import BoundingBox
from src.domain.ports.vision import IAnchorDetector


class AnchorDetector(IAnchorDetector):
    """Detects UI anchors: Like-Comment-Share bar and Like-Reply buttons."""

    def __init__(self, model_weights_path: Optional[str] = None):
        self.model_weights_path = model_weights_path

    def detect_post_anchor(self, card_image: Any) -> Optional[BoundingBox]:
        if card_image is None or not isinstance(card_image, np.ndarray):
            return None

        h, w, _ = card_image.shape
        # Default placeholder anchor region near the lower third of card
        anchor_y = max(0, int(h * 0.75))
        anchor_h = min(40, h - anchor_y)
        return BoundingBox(x=10, y=anchor_y, width=w - 20, height=anchor_h)

    def detect_reply_buttons(self, thread_image: Any) -> List[BoundingBox]:
        if thread_image is None or not isinstance(thread_image, np.ndarray):
            return []
        return []
