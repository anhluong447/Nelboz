import numpy as np
import pytest
from src.domain.entities.geometry import BoundingBox, Point
from src.infrastructure.vision.feed_card_segmenter import FeedCardSegmenter
from src.infrastructure.vision.anchor_detector import AnchorDetector
from src.infrastructure.vision.comment_grouper import CommentThreadGrouper


def test_feed_card_segmenter_empty_or_none():
    segmenter = FeedCardSegmenter()
    assert segmenter.segment_cards(None) == []
    assert segmenter.segment_cards(np.zeros((50, 50, 3), dtype=np.uint8)) == []


def test_feed_card_segmenter_synthetic_cards():
    segmenter = FeedCardSegmenter(viewport_y_start=100, min_gap_height=5, min_card_height=50)

    # Create synthetic image of size 600x1300
    img = np.full((600, 1300, 3), 255, dtype=np.uint8)  # white cards

    # Insert gap band at Y=250..260 with color [247, 244, 242]
    bg_color = np.array([247, 244, 242], dtype=np.uint8)
    img[250:260, :, :] = bg_color

    # Insert second gap band at Y=450..460
    img[450:460, :, :] = bg_color

    cards = segmenter.segment_cards(img)
    assert len(cards) == 3

    # Card 1: 100..250 (height 150)
    assert cards[0].y == 100
    assert cards[0].bottom == 250
    assert cards[0].height == 150

    # Card 2: 260..450 (height 190)
    assert cards[1].y == 260
    assert cards[1].bottom == 450
    assert cards[1].height == 190

    # Card 3: 460..600 (height 140)
    assert cards[2].y == 460
    assert cards[2].bottom == 600
    assert cards[2].height == 140


def test_anchor_detector_empty_or_none():
    detector = AnchorDetector()
    assert detector.detect_post_anchor(None) is None
    assert detector.detect_post_anchor(np.zeros((10, 10, 3), dtype=np.uint8)) is None
    assert detector.detect_feed_anchors(None) == []
    assert detector.detect_reply_buttons(None) == []


def test_anchor_detector_comment_click_geometry():
    detector = AnchorDetector()
    anchor = BoundingBox(x=627, y=500, width=637, height=36)
    # Fallback when no image is provided
    click_pt = detector.get_comment_button_center(anchor)
    assert click_pt.x == 627 + 65
    assert click_pt.y == 500 + 16


def test_comment_grouper_hierarchy():
    grouper = CommentThreadGrouper(indent_threshold_px=75)

    # When given None or empty
    assert grouper.group_comments(None) == []
    assert grouper.group_comments(np.zeros((10, 10, 3), dtype=np.uint8)) == []
