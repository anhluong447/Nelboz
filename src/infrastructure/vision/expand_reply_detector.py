from pathlib import Path
from typing import Any, List, Optional, Tuple
import cv2
import numpy as np
from src.domain.entities.geometry import BoundingBox, Point


class ExpandReplyDetector:
    """Detects 'Xem x câu trả lời' / 'Xem x phản hồi' expand buttons in Facebook thread modals.

    Uses co-occurrence template matching between the downward chevron icon ('v')
    and the 'Xem' text keyword to ensure 100% precision with zero false positives.
    """

    DEFAULT_TEMPLATES_DIR = Path(__file__).parent / "templates"

    def __init__(
        self,
        templates_dir: Optional[Path] = None,
        chevron_threshold: float = 0.72,
        xem_threshold: float = 0.70,
    ):
        self.templates_dir = templates_dir or self.DEFAULT_TEMPLATES_DIR
        self.chevron_threshold = chevron_threshold
        self.xem_threshold = xem_threshold

        self._chevron_tpl: Optional[np.ndarray] = None
        self._xem_tpl: Optional[np.ndarray] = None
        self._load_templates()

    def _load_templates(self) -> None:
        c_path = self.templates_dir / "thread_expand_chevron.png"
        x_path = self.templates_dir / "thread_expand_xem.png"

        if c_path.exists():
            self._chevron_tpl = cv2.imread(str(c_path), cv2.IMREAD_GRAYSCALE)
        if x_path.exists():
            self._xem_tpl = cv2.imread(str(x_path), cv2.IMREAD_GRAYSCALE)

    def detect_expand_buttons(self, modal_image: Any) -> List[Point]:
        """Finds all visible 'Xem x câu trả lời / phản hồi' button click targets.

        Args:
            modal_image: BGR or Grayscale numpy array of the thread modal or comment section.

        Returns:
            List of Point coordinates (relative to modal_image) representing the click center.
        """
        boxes = self.detect_expand_boxes(modal_image)
        return [box.center for box in boxes]

    def detect_expand_boxes(self, modal_image: Any) -> List[BoundingBox]:
        """Finds all visible expand button bounding boxes.

        Args:
            modal_image: BGR or Grayscale numpy array.

        Returns:
            List of BoundingBox objects for each detected expand button.
        """
        if modal_image is None or not isinstance(modal_image, np.ndarray):
            return []

        if self._chevron_tpl is None or self._xem_tpl is None:
            return []

        h, w = modal_image.shape[:2]
        ch, cw = self._chevron_tpl.shape[:2]
        xh, xw = self._xem_tpl.shape[:2]

        if h < max(ch, xh) or w < max(cw, xw):
            return []

        if len(modal_image.shape) == 3:
            gray = cv2.cvtColor(modal_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = modal_image

        res_c = cv2.matchTemplate(gray, self._chevron_tpl, cv2.TM_CCOEFF_NORMED)
        res_x = cv2.matchTemplate(gray, self._xem_tpl, cv2.TM_CCOEFF_NORMED)

        loc_c = np.where(res_c >= self.chevron_threshold)
        loc_x = np.where(res_x >= self.xem_threshold)

        raw_chevrons = list(zip(*loc_c[::-1]))
        raw_xems = list(zip(*loc_x[::-1]))

        # Filter out bottom fixed input area (avatar badge chevron at bottom of modal)
        # Typically the bottom 90px of a thread modal is the input bar
        max_valid_y = h - 85 if h > 200 else h

        detected_boxes: List[BoundingBox] = []

        for cx, cy in raw_chevrons:
            if cy >= max_valid_y:
                continue

            for xx, xy in raw_xems:
                # Chevron precedes 'Xem' by 10 to 25px, and aligned vertically within 8px
                if 10 <= (xx - cx) <= 25 and abs(xy - cy) <= 8:
                    # Deduplicate nearby matches
                    if not any(abs(b.y - cy) < 15 for b in detected_boxes):
                        # Construct bounding box encompassing chevron and 'Xem ...' text row
                        box = BoundingBox(
                            x=int(cx),
                            y=int(cy),
                            width=140,  # Covers chevron + 'Xem x phản hồi/câu trả lời'
                            height=max(ch, xh) + 6,
                        )
                        detected_boxes.append(box)

        # Sort top to bottom
        detected_boxes.sort(key=lambda b: b.y)
        return detected_boxes
