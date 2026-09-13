import unittest
from typing import Any, List, Optional
import numpy as np

from src.config.settings import AppConfig
from src.domain.entities.geometry import BoundingBox, Point
from src.domain.entities.window import WindowInfo
from src.domain.entities.decision import ActionDecision, ActionType
from src.domain.entities.comment import CommentUnit
from src.domain.ports.window import IWindowManager
from src.domain.ports.capture import IScreenCapture
from src.domain.ports.vision import ICardSegmenter, IAnchorDetector, ICommentGrouper
from src.domain.ports.ocr import ITextRecognizer
from src.domain.ports.filter import ITextFilter
from src.domain.ports.llm import ILLMClient
from src.domain.ports.input import IInputController
from src.domain.ports.limiter import IRateLimiter
from src.application.use_cases.feed_comment_flow import FeedCommentUseCase
from src.application.use_cases.thread_reply_flow import ThreadReplyUseCase
from src.application.dto.context_dto import FlowAExecutionContext, FlowBExecutionContext


class DummyWindowManager(IWindowManager):
    def find_target_window(self, title_pattern: str) -> Optional[WindowInfo]:
        return WindowInfo(
            hwnd=12345,
            title="Google Chrome - Facebook",
            rect=BoundingBox(0, 0, 1920, 1080),
            is_active=True,
        )

    def is_window_active(self, hwnd: int) -> bool:
        return True

    def focus_window(self, hwnd: int) -> bool:
        return True


class DummyScreenCapture(IScreenCapture):
    def capture_region(self, region: BoundingBox) -> Any:
        return np.zeros((region.height, region.width, 3), dtype=np.uint8)

    def capture_window(self, window: WindowInfo) -> Any:
        return np.zeros((window.rect.height, window.rect.width, 3), dtype=np.uint8)

    def capture_fullscreen(self) -> Any:
        return np.zeros((1080, 1920, 3), dtype=np.uint8)



class DummyCardSegmenter(ICardSegmenter):
    def segment_cards(self, feed_image: Any) -> List[BoundingBox]:
        return [BoundingBox(100, 100, 600, 400)]


class DummyAnchorDetector(IAnchorDetector):
    def detect_post_anchor(self, card_image: Any) -> Optional[BoundingBox]:
        return BoundingBox(10, 300, 580, 40)

    def detect_reply_buttons(self, thread_image: Any) -> List[BoundingBox]:
        return [BoundingBox(50, 60, 40, 20)]

    def get_comment_button_center(self, anchor_box: BoundingBox) -> Point:
        return Point(anchor_box.x + 41, anchor_box.y + 16)


class DummyOCR(ITextRecognizer):
    def recognize_text(self, image_crop: Any) -> str:
        return "Nội dung bài viết mẫu thảo luận công nghệ rất hay."


class DummyFilter(ITextFilter):
    def should_process(self, text: str) -> bool:
        return True


class DummyLLM(ILLMClient):
    def evaluate_and_generate(
        self, context_text: str, action_type: ActionType, thread_context: Optional[str] = None
    ) -> ActionDecision:
        return ActionDecision(
            should_act=True,
            text="Bài viết rất hữu ích!",
            action_type=action_type,
            reason="Good tech post",
        )


class DummyInput(IInputController):
    def __init__(self):
        self.clicked_points: List[Point] = []
        self.typed_texts: List[str] = []
        self.pressed_keys: List[str] = []
        self.cleared_count: int = 0

    def move_to(self, target: Point) -> None:
        pass

    def click(self, target: Optional[Point] = None) -> None:
        if target:
            self.clicked_points.append(target)

    def type_text(self, text: str) -> None:
        self.typed_texts.append(text)

    def press_key(self, key_name: str) -> None:
        self.pressed_keys.append(key_name)

    def scroll(self, clicks: int) -> None:
        pass

    def clear_input(self) -> None:
        self.cleared_count += 1

    def sleep_random(self, min_sec: float, max_sec: float) -> None:
        pass


class DummyLimiter(IRateLimiter):
    def __init__(self):
        self.records: List[str] = []

    def can_perform(self, action_key: str) -> bool:
        return True

    def record_action(self, action_key: str) -> None:
        self.records.append(action_key)

    def wait_if_needed(self, action_key: str) -> None:
        pass


class DummyCommentGrouper(ICommentGrouper):
    def group_comments(self, thread_image: Any) -> List[CommentUnit]:
        return [
            CommentUnit(
                id="comment_1",
                unit_box=BoundingBox(20, 20, 400, 100),
                text_box=BoundingBox(20, 20, 400, 60),
                reply_button_box=BoundingBox(50, 80, 40, 20),
                level=1,
            )
        ]


class TestUseCases(unittest.TestCase):
    def test_feed_comment_use_case_flow(self):
        config = AppConfig()
        input_ctrl = DummyInput()
        limiter = DummyLimiter()

        use_case = FeedCommentUseCase(
            config=config,
            window_mgr=DummyWindowManager(),
            capture=DummyScreenCapture(),
            card_segmenter=DummyCardSegmenter(),
            anchor_detector=DummyAnchorDetector(),
            ocr=DummyOCR(),
            text_filter=DummyFilter(),
            llm=DummyLLM(),
            input_ctrl=input_ctrl,
            limiter=limiter,
        )

        ctx = FlowAExecutionContext()
        acted = use_case.execute_step(ctx)

        self.assertTrue(acted)
        self.assertEqual(ctx.comments_submitted, 1)
        self.assertIn("Bài viết rất hữu ích!", input_ctrl.typed_texts)
        self.assertIn("enter", input_ctrl.pressed_keys)
        self.assertIn("flow_a_comment", limiter.records)

    def test_feed_comment_use_case_dry_run(self):
        config = AppConfig(dry_run=True)
        input_ctrl = DummyInput()
        limiter = DummyLimiter()

        use_case = FeedCommentUseCase(
            config=config,
            window_mgr=DummyWindowManager(),
            capture=DummyScreenCapture(),
            card_segmenter=DummyCardSegmenter(),
            anchor_detector=DummyAnchorDetector(),
            ocr=DummyOCR(),
            text_filter=DummyFilter(),
            llm=DummyLLM(),
            input_ctrl=input_ctrl,
            limiter=limiter,
        )

        ctx = FlowAExecutionContext()
        acted = use_case.execute_step(ctx)

        self.assertTrue(acted)
        # In dry run, comments are not counted as submitted to FB
        self.assertEqual(ctx.comments_submitted, 0)
        self.assertIn("Bài viết rất hữu ích!", input_ctrl.typed_texts)
        # In dry run, Enter is NEVER pressed!
        self.assertNotIn("enter", input_ctrl.pressed_keys)
        # Text is cleared with clear_input()
        self.assertEqual(input_ctrl.cleared_count, 1)
        # Limiter is not consumed
        self.assertNotIn("flow_a_comment", limiter.records)

    def test_thread_reply_use_case_flow(self):
        config = AppConfig()
        input_ctrl = DummyInput()
        limiter = DummyLimiter()

        use_case = ThreadReplyUseCase(
            config=config,
            window_mgr=DummyWindowManager(),
            capture=DummyScreenCapture(),
            comment_grouper=DummyCommentGrouper(),
            ocr=DummyOCR(),
            text_filter=DummyFilter(),
            llm=DummyLLM(),
            input_ctrl=input_ctrl,
            limiter=limiter,
        )

        ctx = FlowBExecutionContext()
        acted = use_case.execute_step(post_context_text="Post title", context=ctx)

        self.assertTrue(acted)
        self.assertEqual(ctx.replies_submitted, 1)
        self.assertIn("Bài viết rất hữu ích!", input_ctrl.typed_texts)
        self.assertIn("flow_b_reply", limiter.records)

