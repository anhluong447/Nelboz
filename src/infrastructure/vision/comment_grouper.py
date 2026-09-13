from pathlib import Path
from typing import Any, List, Optional, Tuple
import cv2
import numpy as np
from src.domain.entities.geometry import BoundingBox
from src.domain.entities.comment import CommentUnit
from src.domain.ports.vision import ICommentGrouper


class CommentThreadGrouper(ICommentGrouper):
    """Detects and groups comments into structured CommentUnit hierarchies.

    Identifies top-level comments (Level 1) and nested replies (Level 2)
    using horizontal indentation (threshold ~75px) and associates each comment
    with its specific 'Reply' ('Trả lời') button anchor (+82px from Like icon).
    """

    DEFAULT_TEMPLATES_DIR = Path(__file__).parent / "templates"

    def __init__(
        self,
        templates_dir: Optional[Path] = None,
        indent_threshold_px: int = 75,
        match_threshold: float = 0.68,
    ):
        self.templates_dir = templates_dir or self.DEFAULT_TEMPLATES_DIR
        self.indent_threshold_px = indent_threshold_px
        self.match_threshold = match_threshold

        self._like_tpl: Optional[np.ndarray] = None
        self._load_template()

    def _load_template(self) -> None:
        tpl_path = self.templates_dir / "thread_like.png"
        if tpl_path.exists():
            self._like_tpl = cv2.imread(str(tpl_path), cv2.IMREAD_GRAYSCALE)

    def group_comments(self, thread_image: Any) -> List[CommentUnit]:
        """Detects and groups comments with their corresponding reply anchors and nested levels.

        Args:
            thread_image: BGR numpy image of the comment thread or modal.

        Returns:
            List of CommentUnit entities sorted in reading order.
        """
        if thread_image is None or not isinstance(thread_image, np.ndarray):
            return []

        if self._like_tpl is None:
            return []

        h, w = thread_image.shape[:2]
        th, tw = self._like_tpl.shape[:2]

        if h < th or w < tw:
            return []

        if len(thread_image.shape) == 3:
            gray = cv2.cvtColor(thread_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = thread_image

        res = cv2.matchTemplate(gray, self._like_tpl, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= self.match_threshold)

        raw_points: List[Tuple[int, int]] = []
        for pt in zip(*loc[::-1]):
            if not any(abs(pt[0] - p[0]) < 15 and abs(pt[1] - p[1]) < 15 for p in raw_points):
                raw_points.append((int(pt[0]), int(pt[1])))

        # Sort top-to-bottom
        raw_points.sort(key=lambda p: p[1])

        comment_units: List[CommentUnit] = []
        current_l1_id: Optional[str] = None
        prev_anchor_bottom = 0

        for i, (lx, ly) in enumerate(raw_points):
            unit_id = f"comment_{i+1:03d}"
            is_reply = lx > self.indent_threshold_px
            level = 2 if is_reply else 1

            if level == 1:
                current_l1_id = unit_id
                parent_id = None
            else:
                parent_id = current_l1_id

            # Reply button is located +82px to the right of the Like icon center
            reply_btn_x = lx + 82
            reply_btn_y = ly + th // 2
            reply_btn_box = BoundingBox(
                x=reply_btn_x - 22,
                y=reply_btn_y - 10,
                width=44,
                height=20,
            )

            # Estimate comment unit boundary and text box
            unit_top = max(prev_anchor_bottom, ly - 70)
            unit_bottom = ly + th + 10
            unit_left = max(0, lx - 45)  # include avatar
            unit_width = min(w - unit_left, 550)

            unit_box = BoundingBox(
                x=unit_left,
                y=unit_top,
                width=unit_width,
                height=unit_bottom - unit_top,
            )

            # Text box sits above the like/reply anchor row
            text_box = BoundingBox(
                x=lx,
                y=unit_top,
                width=max(50, unit_width - (lx - unit_left)),
                height=max(20, ly - unit_top),
            )

            unit = CommentUnit(
                id=unit_id,
                unit_box=unit_box,
                level=level,
                text_box=text_box,
                reply_button_box=reply_btn_box,
                parent_id=parent_id,
            )
            comment_units.append(unit)
            prev_anchor_bottom = unit_bottom

        return comment_units
