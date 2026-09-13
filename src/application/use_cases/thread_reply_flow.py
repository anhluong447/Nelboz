import logging
import random
from typing import Optional

from src.config.settings import AppConfig
from src.domain.entities.geometry import Point
from src.domain.entities.decision import ActionType
from src.domain.ports.capture import IScreenCapture
from src.domain.ports.window import IWindowManager
from src.domain.ports.vision import ICommentGrouper
from src.domain.ports.ocr import ITextRecognizer
from src.domain.ports.filter import ITextFilter
from src.domain.ports.llm import ILLMClient
from src.domain.ports.input import IInputController
from src.domain.ports.limiter import IRateLimiter
from src.application.dto.context_dto import FlowBExecutionContext

logger = logging.getLogger(__name__)


class ThreadReplyUseCase:
    """FLOW B: Replying to specific comments within a post thread."""

    def __init__(
        self,
        config: AppConfig,
        window_mgr: IWindowManager,
        capture: IScreenCapture,
        comment_grouper: ICommentGrouper,
        ocr: ITextRecognizer,
        text_filter: ITextFilter,
        llm: ILLMClient,
        input_ctrl: IInputController,
        limiter: IRateLimiter,
    ):
        self.config = config
        self.window_mgr = window_mgr
        self.capture = capture
        self.comment_grouper = comment_grouper
        self.ocr = ocr
        self.text_filter = text_filter
        self.llm = llm
        self.input_ctrl = input_ctrl
        self.limiter = limiter

    def execute_step(
        self,
        post_context_text: str = "",
        context: Optional[FlowBExecutionContext] = None,
    ) -> bool:
        """Executes a single step/cycle of Flow B (Reply thread).

        Returns True if a reply was posted.
        """
        ctx = context or FlowBExecutionContext()

        window = self.window_mgr.find_target_window(self.config.target_window.title_pattern)
        if not window:
            logger.warning("Target window (Chrome) not found.")
            ctx.errors.append("Chrome window not found")
            return False

        if not self.window_mgr.is_window_active(window.hwnd):
            self.window_mgr.focus_window(window.hwnd)
            self.input_ctrl.sleep_random(0.5, 1.0)

        # 1. Capture thread viewport
        viewport_img = self.capture.capture_window(window)
        if viewport_img is None:
            return False

        # 2. Group comments into CommentUnits (text + reply button + hierarchy)
        comment_units = self.comment_grouper.group_comments(viewport_img)
        if not comment_units:
            logger.info("No comment units identified in current view.")
            return False

        logger.info("Identified %d comment units in thread.", len(comment_units))

        # Check thread limit
        if ctx.replies_submitted >= self.config.flow_b.max_replies_per_thread:
            logger.info("Reached maximum replies for this thread (%d).", ctx.replies_submitted)
            return False

        # 3. Iterate through comment units
        for unit in comment_units:
            ctx.comments_inspected += 1

            if not unit.reply_button_box or not unit.text_box:
                continue

            # Convert to absolute screen coordinates
            abs_text_box = unit.text_box.offset(window.rect.x, window.rect.y)
            abs_reply_box = unit.reply_button_box.offset(window.rect.x, window.rect.y)

            # OCR comment text
            crop_img = self.capture.capture_region(abs_text_box)
            comment_text = self.ocr.recognize_text(crop_img).strip()

            if not comment_text or not self.text_filter.should_process(comment_text):
                continue

            # Check rate limiter
            if not self.limiter.can_perform("flow_b_reply"):
                logger.info("Rate limit reached for Flow B.")
                return False

            # LLM evaluation with combined context
            decision = self.llm.evaluate_and_generate(
                context_text=comment_text,
                action_type=ActionType.REPLY,
                thread_context=post_context_text,
            )

            if not decision.should_act or not decision.text:
                continue

            # Click EXACT reply button for this comment unit
            reply_target = Point(
                x=abs_reply_box.center.x + random.randint(-4, 4),
                y=abs_reply_box.center.y + random.randint(-2, 2),
            )
            logger.info("Clicking reply button for comment unit: %s", unit.id)
            self.input_ctrl.move_to(reply_target)
            self.input_ctrl.sleep_random(0.2, 0.4)
            self.input_ctrl.click(reply_target)
            self.input_ctrl.sleep_random(0.8, 1.5)

            # Type reply and enter
            logger.info("Typing reply: '%s'...", decision.text)
            self.input_ctrl.type_text(decision.text)
            self.input_ctrl.sleep_random(0.4, 0.8)
            self.input_ctrl.press_key("enter")

            # Record
            self.limiter.record_action("flow_b_reply")
            ctx.replies_submitted += 1
            self.input_ctrl.sleep_random(3.0, 6.0)
            return True

        return False
