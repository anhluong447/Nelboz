from pathlib import Path
import cv2
import numpy as np
import pytest
from src.domain.entities.geometry import Point
from src.infrastructure.vision.expand_reply_detector import ExpandReplyDetector


def test_expand_reply_detector_empty_or_none():
    detector = ExpandReplyDetector()
    assert detector.detect_expand_buttons(None) == []
    assert detector.detect_expand_buttons(np.zeros((10, 10, 3), dtype=np.uint8)) == []
    assert detector.detect_expand_boxes(None) == []
    assert detector.detect_expand_boxes(np.zeros((10, 10, 3), dtype=np.uint8)) == []


def test_expand_reply_detector_on_modal_samples():
    detector = ExpandReplyDetector()

    modal_00_path = Path("data/raw_samples/threads/modal_00.png")
    if modal_00_path.exists():
        img = cv2.imread(str(modal_00_path))
        boxes = detector.detect_expand_boxes(img)
        points = detector.detect_expand_buttons(img)

        # In modal_00, there are 2 expand buttons ('Xem 1 phản hồi')
        assert len(boxes) == 2
        assert len(points) == 2

        # Verify boxes have valid dimensions
        for box in boxes:
            assert box.x >= 50
            assert box.y >= 300
            assert box.width > 50
            assert box.height >= 12

        # Verify points are within modal bounds
        for pt in points:
            assert isinstance(pt, Point)
            assert 0 <= pt.x <= img.shape[1]
            assert 0 <= pt.y <= img.shape[0]


def test_expand_reply_detector_modal_without_expand():
    detector = ExpandReplyDetector()

    modal_05_path = Path("data/raw_samples/threads/modal_05.png")
    if modal_05_path.exists():
        img = cv2.imread(str(modal_05_path))
        boxes = detector.detect_expand_boxes(img)
        # modal_05 does not contain expand buttons in comments area
        assert len(boxes) == 0
