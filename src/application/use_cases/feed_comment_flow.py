import logging
import random
from typing import Optional

from src.config.settings import AppConfig
from src.domain.entities.geometry import Point, BoundingBox
from src.domain.entities.decision import ActionType
from src.domain.entities.post import PostCard
from src.domain.ports.capture import IScreenCapture
from src.domain.ports.window import IWindowManager
from src.domain.ports.vision import ICardSegmenter, IAnchorDetector
from src.domain.ports.ocr import ITextRecognizer
from src.domain.ports.filter import ITextFilter
from src.domain.ports.llm import ILLMClient
from src.domain.ports.input import IInputController
from src.domain.ports.limiter import IRateLimiter
from src.application.dto.context_dto import FlowAExecutionContext

logger = logging.getLogger(__name__)


class FeedCommentUseCase:
    """FLOW A: Commenting on new feed posts."""

    def __init__(
        self,
        config: AppConfig,
        window_mgr: IWindowManager,
        capture: IScreenCapture,
        card_segmenter: ICardSegmenter,
        anchor_detector: IAnchorDetector,
        ocr: ITextRecognizer,
        text_filter: ITextFilter,
        llm: ILLMClient,
        input_ctrl: IInputController,
        limiter: IRateLimiter,
    ):
        self.config = config
        self.window_mgr = window_mgr
        self.capture = capture
        self.card_segmenter = card_segmenter
        self.anchor_detector = anchor_detector
        self.ocr = ocr
        self.text_filter = text_filter
        self.llm = llm
        self.input_ctrl = input_ctrl
        self.limiter = limiter

    def execute_step(self, context: Optional[FlowAExecutionContext] = None) -> bool:
        """Executes a single step/cycle of Flow A.

        Returns True if a comment was posted, False otherwise.
        """
        ctx = context or FlowAExecutionContext()

        # 1. Verify target window
        window = self.window_mgr.find_target_window(self.config.target_window.title_pattern)
        if not window:
            logger.warning("Target window (Chrome) not found.")
            ctx.errors.append("Chrome window not found")
            return False

        if not self.window_mgr.is_window_active(window.hwnd):
            logger.info("Chrome is not active window. Focusing...")
            self.window_mgr.focus_window(window.hwnd)
            self.input_ctrl.sleep_random(0.5, 1.0)

        # 2. Capture viewport
        viewport_img = self.capture.capture_window(window)
        if viewport_img is None:
            logger.warning("Failed to capture viewport.")
            return False

        # 3. Background-segmentation to find cards
        card_boxes = self.card_segmenter.segment_cards(viewport_img)
        if not card_boxes:
            logger.info("No post cards detected in view. Scrolling...")
            self._scroll_next()
            return False

        logger.info("Found %d post cards in current view.", len(card_boxes))

        # 4. Process each detected card
        for card_box in card_boxes:
            ctx.cards_inspected += 1

            # Convert card box relative coordinates to screen coordinates
            abs_card_box = card_box.offset(window.rect.x, window.rect.y)

            # Crop card image from viewport
            card_img = self.capture.capture_region(abs_card_box)
            if card_img is None:
                continue

            # 5. Detect Like-Comment-Share anchor
            anchor_box = self.anchor_detector.detect_post_anchor(card_img)
            if not anchor_box:
                logger.debug("Anchor Like-Comment-Share not found in card. Skipping.")
                continue

            # 6. Crop text area above anchor
            text_region = BoundingBox(
                x=abs_card_box.x,
                y=abs_card_box.y,
                width=abs_card_box.width,
                height=max(10, anchor_box.y),
            )
            text_img = self.capture.capture_region(text_region)
            raw_text = self.ocr.recognize_text(text_img).strip()

            logger.debug("Extracted text: %s", raw_text[:60] if raw_text else "(empty)")

            # 7. Cheap NLP filter
            if not raw_text or not self.text_filter.should_process(raw_text):
                logger.info("Card text filtered out by cheap filter. Skipping.")
                ctx.skipped_count += 1
                continue

            # 8. Check rate limiter
            if not self.limiter.can_perform("flow_a_comment"):
                logger.info("Rate limit reached for Flow A. Waiting or skipping.")
                return False

            # 9. LLM decision & generation
            decision = self.llm.evaluate_and_generate(
                context_text=raw_text,
                action_type=ActionType.COMMENT,
            )

            if not decision.should_act or not decision.text:
                logger.info("LLM decided to skip this post. Reason: %s", decision.reason)
                ctx.skipped_count += 1
                continue

            # 10. Compute comment box coordinate using AnchorDetector (+41px from Like icon)
            comment_click_pt = self.anchor_detector.get_comment_button_center(anchor_box.offset(abs_card_box.x, abs_card_box.y))

            # 11. Human-like simulation
            logger.info("Target comment button at (%d, %d)", comment_click_pt.x, comment_click_pt.y)
            self.input_ctrl.move_to(comment_click_pt)
            self.input_ctrl.sleep_random(0.2, 0.5)
            self.input_ctrl.click(comment_click_pt)
            self.input_ctrl.sleep_random(0.6, 1.2)

            logger.info("Typing comment draft: '%s'...", decision.text)
            self.input_ctrl.type_text(decision.text)
            self.input_ctrl.sleep_random(1.2, 2.0)

            if self.config.dry_run:
                logger.info("[DRY-RUN] Text typed for observation. Clearing input field without submitting...")
                self.input_ctrl.clear_input()
                self.input_ctrl.sleep_random(0.5, 1.0)
            else:
                self.input_ctrl.press_key("enter")
                self.limiter.record_action("flow_a_comment")
                ctx.comments_submitted += 1

            self.input_ctrl.sleep_random(2.0, 3.5)
            self._scroll_next()
            return True

        # If all cards inspected without action, scroll down
        self._scroll_next()
        return False

    def _scroll_next(self) -> None:
        scroll_px = random.randint(
            self.config.flow_a.scroll_min_px,
            self.config.flow_a.scroll_max_px,
        )
        self.input_ctrl.scroll(-scroll_px)
        self.input_ctrl.sleep_random(1.5, 3.0)


def comment_click_target(center_x: int) -> int:
    return center_x + random.randint(-20, 20)
