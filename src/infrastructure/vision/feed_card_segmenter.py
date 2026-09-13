from typing import Any, List, Tuple
import numpy as np
from src.domain.entities.geometry import BoundingBox
from src.domain.ports.vision import ICardSegmenter


class FeedCardSegmenter(ICardSegmenter):
    """Segments individual Facebook post cards from feed screenshots using background-gap profiling.

    Facebook post cards on desktop (Cốc Cốc / Chromium at 1920x1080 @ 125% DPI)
    are separated by horizontal gap bands colored #F0F2F5 (BGR ~ [247, 244, 242]).
    By scanning row-wise across the feed column and its immediate borders,
    we identify continuous gap bands (height 8-10px) to delineate card boundaries.
    """

    DEFAULT_CARD_X: int = 617
    DEFAULT_CARD_WIDTH: int = 637  # 1254 - 617
    DEFAULT_SCAN_X_START: int = 605
    DEFAULT_SCAN_X_END: int = 1265
    DEFAULT_BG_COLOR: Tuple[int, int, int] = (247, 244, 242)  # BGR
    DEFAULT_BG_TOLERANCE: int = 7
    DEFAULT_VIEWPORT_Y_START: int = 160
    DEFAULT_MIN_GAP_HEIGHT: int = 6
    DEFAULT_MIN_CARD_HEIGHT: int = 80

    def __init__(
        self,
        card_x: int = DEFAULT_CARD_X,
        card_width: int = DEFAULT_CARD_WIDTH,
        scan_x_start: int = DEFAULT_SCAN_X_START,
        scan_x_end: int = DEFAULT_SCAN_X_END,
        bg_color: Tuple[int, int, int] = DEFAULT_BG_COLOR,
        bg_tolerance: int = DEFAULT_BG_TOLERANCE,
        viewport_y_start: int = DEFAULT_VIEWPORT_Y_START,
        min_gap_height: int = DEFAULT_MIN_GAP_HEIGHT,
        min_card_height: int = DEFAULT_MIN_CARD_HEIGHT,
    ):
        self.card_x = card_x
        self.card_width = card_width
        self.scan_x_start = scan_x_start
        self.scan_x_end = scan_x_end
        self.bg_color = np.array(bg_color, dtype=np.int32)
        self.bg_tolerance = bg_tolerance
        self.viewport_y_start = viewport_y_start
        self.min_gap_height = min_gap_height
        self.min_card_height = min_card_height

    def find_gap_intervals(self, feed_image: np.ndarray) -> List[Tuple[int, int]]:
        """Identifies vertical ranges (y_start, y_end) of feed separator bands."""
        h, w, _ = feed_image.shape
        y_start = min(self.viewport_y_start, h)
        if y_start >= h:
            return []

        x1 = max(0, self.scan_x_start)
        x2 = min(w, self.scan_x_end)
        if x2 <= x1:
            return []

        # Crop region of interest across feed borders
        roi = feed_image[y_start:h, x1:x2, :].astype(np.int32)
        diff = np.abs(roi - self.bg_color)
        is_bg = np.all(diff <= self.bg_tolerance, axis=2)
        row_bg_ratio = np.mean(is_bg, axis=1)

        # Gap rows must have overwhelming background match (> 90%)
        is_gap_row = row_bg_ratio > 0.90
        gap_indices = np.where(is_gap_row)[0] + y_start

        if len(gap_indices) == 0:
            return []

        # Cluster contiguous gap rows
        raw_intervals: List[Tuple[int, int]] = []
        g_start = gap_indices[0]
        prev = gap_indices[0]

        for g in gap_indices[1:]:
            if g == prev + 1:
                prev = g
            else:
                raw_intervals.append((int(g_start), int(prev)))
                g_start = g
                prev = g
        raw_intervals.append((int(g_start), int(prev)))

        # Filter intervals by minimum gap height
        valid_intervals = [
            (s, e) for (s, e) in raw_intervals if (e - s + 1) >= self.min_gap_height
        ]
        return valid_intervals

    def segment_cards(self, feed_image: Any) -> List[BoundingBox]:
        """Segments individual post cards from the feed image.

        Args:
            feed_image: BGR numpy image of the screen / feed.

        Returns:
            List of BoundingBox objects for each detected post card.
        """
        if feed_image is None or not isinstance(feed_image, np.ndarray):
            return []

        if len(feed_image.shape) != 3:
            return []

        h, w, _ = feed_image.shape
        if h < self.viewport_y_start + self.min_card_height:
            return []

        gaps = self.find_gap_intervals(feed_image)

        card_intervals: List[Tuple[int, int]] = []
        current_y = self.viewport_y_start

        for gap_start, gap_end in gaps:
            if gap_start - current_y >= self.min_card_height:
                card_intervals.append((current_y, gap_start))
            current_y = gap_end + 1

        if h - current_y >= self.min_card_height:
            card_intervals.append((current_y, h))

        # Fallback if no valid gaps detected: treat entire column as single card
        if not card_intervals:
            card_intervals.append((self.viewport_y_start, h))

        card_boxes: List[BoundingBox] = []
        for top, bottom in card_intervals:
            box = BoundingBox(
                x=self.card_x,
                y=top,
                width=self.card_width,
                height=bottom - top,
            )
            card_boxes.append(box)

        return card_boxes
