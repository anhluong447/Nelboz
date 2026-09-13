import os
from pathlib import Path
from typing import Any, List, Optional, Tuple
import cv2
import numpy as np
from src.domain.entities.geometry import BoundingBox, Point
from src.domain.ports.vision import IAnchorDetector


class AnchorDetector(IAnchorDetector):
    """Detects UI anchors in Facebook feed cards and comment threads.

    - Flow A: Detects Like-Comment-Share action bar in post cards.
    - Flow B: Detects Like-Reply buttons in comment thread modals.
    """

    DEFAULT_TEMPLATES_DIR = Path(__file__).parent / "templates"

    def __init__(
        self,
        templates_dir: Optional[Path] = None,
        feed_like_threshold: float = 0.70,
        thread_like_threshold: float = 0.65,
    ):
        self.templates_dir = templates_dir or self.DEFAULT_TEMPLATES_DIR
        self.feed_like_threshold = feed_like_threshold
        self.thread_like_threshold = thread_like_threshold

        self._feed_like_tpl: Optional[np.ndarray] = None
        self._thread_like_tpl: Optional[np.ndarray] = None
        self._load_templates()

    def _load_templates(self) -> None:
        feed_path = self.templates_dir / "feed_like.png"
        thread_path = self.templates_dir / "thread_like.png"

        if feed_path.exists():
            self._feed_like_tpl = cv2.imread(str(feed_path), cv2.IMREAD_GRAYSCALE)
        if thread_path.exists():
            self._thread_like_tpl = cv2.imread(str(thread_path), cv2.IMREAD_GRAYSCALE)

    def detect_post_anchor(self, card_image: Any) -> Optional[BoundingBox]:
        """Detects Like-Comment-Share action bar anchor in a post card image.

        Args:
            card_image: BGR numpy image of the post card (or full screen).

        Returns:
            BoundingBox of the detected action bar, or None if not visible.
        """
        if card_image is None or not isinstance(card_image, np.ndarray):
            return None

        if self._feed_like_tpl is None:
            return None

        h, w = card_image.shape[:2]
        th, tw = self._feed_like_tpl.shape[:2]

        if h < th or w < tw:
            return None

        if len(card_image.shape) == 3:
            gray = cv2.cvtColor(card_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = card_image

        # Search region: if full screen (w > 1000), constrain horizontally to feed like col (615..665)
        # If card crop (w ~ 637), search along left margin (0..60)
        if w > 1000:
            x_min, x_max = 615, min(w, 665)
        else:
            x_min, x_max = 0, min(w, 60)

        roi = gray[:, x_min:x_max]
        if roi.shape[0] < th or roi.shape[1] < tw:
            return None

        res = cv2.matchTemplate(roi, self._feed_like_tpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        if max_val < self.feed_like_threshold:
            return None

        best_x = max_loc[0] + x_min
        best_y = max_loc[1]

        # Action bar spans the width of the card (~637px), height ~ 36px
        bar_y = max(0, best_y - 4)
        bar_h = min(36, h - bar_y)
        bar_w = min(637, w - best_x)

        return BoundingBox(
            x=best_x,
            y=bar_y,
            width=bar_w,
            height=bar_h,
        )

    def detect_feed_anchors(self, feed_image: Any, y_min: int = 160, y_max: int = 1080) -> List[BoundingBox]:
        """Detects all Like-Comment-Share action bars visible on the feed viewport.

        Args:
            feed_image: BGR numpy image of the full feed (1920x1080).
            y_min: Top boundary of feed viewport.
            y_max: Bottom boundary of feed viewport.

        Returns:
            List of BoundingBox objects for each detected action bar, sorted top-to-bottom.
        """
        if feed_image is None or not isinstance(feed_image, np.ndarray):
            return []

        if self._feed_like_tpl is None:
            return []

        h, w = feed_image.shape[:2]
        th, tw = self._feed_like_tpl.shape[:2]

        y_top = max(0, y_min)
        y_bottom = min(h, y_max)
        if y_bottom - y_top < th or w < 665:
            return []

        if len(feed_image.shape) == 3:
            gray = cv2.cvtColor(feed_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = feed_image

        roi = gray[y_top:y_bottom, 615:665]
        res = cv2.matchTemplate(roi, self._feed_like_tpl, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= self.feed_like_threshold)

        anchors: List[BoundingBox] = []
        for pt in zip(*loc[::-1]):
            abs_x = pt[0] + 615
            abs_y = pt[1] + y_top
            if not any(abs(abs_y - a.y) < 20 for a in anchors):
                anchors.append(BoundingBox(
                    x=abs_x,
                    y=max(0, abs_y - 4),
                    width=min(637, w - abs_x),
                    height=min(36, h - abs_y),
                ))

        anchors.sort(key=lambda a: a.y)
        return anchors

    def get_comment_button_center(self, anchor_box: BoundingBox) -> Point:
        """Returns the click coordinate for the Comment button relative to the action bar.

        In desktop feed, the comment bubble button is located +41px to the right of the Like icon.
        """
        return Point(x=anchor_box.x + 41, y=anchor_box.y + 16)

    def detect_reply_buttons(self, thread_image: Any) -> List[BoundingBox]:
        """Detects Like-Reply buttons in comment thread modal.

        In thread modal, Reply button is located exactly +82px to the right of Like icon.
        """
        if thread_image is None or not isinstance(thread_image, np.ndarray):
            return []

        if self._thread_like_tpl is None:
            return []

        h, w = thread_image.shape[:2]
        th, tw = self._thread_like_tpl.shape[:2]

        if h < th or w < tw:
            return []

        if len(thread_image.shape) == 3:
            gray = cv2.cvtColor(thread_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = thread_image

        res = cv2.matchTemplate(gray, self._thread_like_tpl, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= self.thread_like_threshold)

        like_points: List[Tuple[int, int]] = []
        for pt in zip(*loc[::-1]):
            # Deduplicate close points
            if not any(abs(pt[0] - p[0]) < 15 and abs(pt[1] - p[1]) < 15 for p in like_points):
                like_points.append(pt)

        # Sort top to bottom
        like_points.sort(key=lambda p: p[1])

        reply_boxes: List[BoundingBox] = []
        for lx, ly in like_points:
            # Reply button is +82px to the right of Like icon center
            reply_x = lx + 82
            reply_y = ly
            reply_boxes.append(BoundingBox(x=reply_x - 10, y=reply_y - 5, width=40, height=20))

        return reply_boxes
