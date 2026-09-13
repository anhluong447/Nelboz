from typing import Optional
from pathlib import Path

from src.config.settings import AppConfig
from src.domain.ports.window import IWindowManager
from src.domain.ports.capture import IScreenCapture
from src.domain.ports.vision import ICardSegmenter, IAnchorDetector, ICommentGrouper
from src.domain.ports.ocr import ITextRecognizer
from src.domain.ports.filter import ITextFilter
from src.domain.ports.llm import ILLMClient
from src.domain.ports.input import IInputController
from src.domain.ports.limiter import IRateLimiter

from src.infrastructure.window.win32_window_manager import Win32WindowManager
from src.infrastructure.capture.mss_screen_capture import MssScreenCapture
from src.infrastructure.vision.feed_card_segmenter import FeedCardSegmenter
from src.infrastructure.vision.anchor_detector import AnchorDetector
from src.infrastructure.vision.comment_grouper import CommentThreadGrouper
from src.infrastructure.ocr.mock_recognizer import MockTextRecognizer
from src.infrastructure.ocr.lens_ocr_recognizer import LensOcrRecognizer
from src.infrastructure.nlp_filter.tfidf_logistic_filter import TfidfLogisticFilter
from src.infrastructure.llm.mock_llm_client import MockLLMClient
from src.infrastructure.llm.cloud_llm_client import CloudLLMClient
from src.infrastructure.input.pynput_controller import PynputHumanController
from src.infrastructure.limiter.sliding_rate_limiter import SlidingRateLimiter


from src.application.use_cases.feed_comment_flow import FeedCommentUseCase
from src.application.use_cases.thread_reply_flow import ThreadReplyUseCase


class Container:
    """Dependency Injection container wiring Domain Ports with Concrete Adapters."""

    def __init__(self, config: Optional[AppConfig] = None, use_mocks: bool = False):
        self.config = config or AppConfig.load_from_yaml(Path("configs/settings.yaml"))
        self.use_mocks = use_mocks

        # Initialize rate limiter
        self.rate_limiter: IRateLimiter = SlidingRateLimiter(
            window_seconds=3600,
            limits={
                "flow_a_comment": self.config.flow_a.max_comments_per_hour,
                "flow_b_reply": self.config.flow_b.max_replies_per_hour,
            },
            min_intervals={
                "flow_a_comment": float(self.config.flow_a.min_interval_seconds),
                "flow_b_reply": float(self.config.flow_b.min_interval_seconds),
            },
        )

        # Window & Capture
        self.window_mgr: IWindowManager = Win32WindowManager(
            dpi_aware=self.config.target_window.dpi_aware
        )
        self.screen_capture: IScreenCapture = MssScreenCapture()

        # Vision
        self.card_segmenter: ICardSegmenter = FeedCardSegmenter()
        self.anchor_detector: IAnchorDetector = AnchorDetector()
        self.comment_grouper: ICommentGrouper = CommentThreadGrouper(
            indent_threshold_px=self.config.flow_b.indent_level_px
        )

        # OCR & Filter
        if not self.use_mocks:
            lens_ocr = LensOcrRecognizer()
            if lens_ocr.is_available():
                self.ocr_recognizer: ITextRecognizer = lens_ocr
            else:
                self.ocr_recognizer = MockTextRecognizer()
        else:
            self.ocr_recognizer = MockTextRecognizer()

        self.text_filter: ITextFilter = TfidfLogisticFilter()


        # LLM
        if not self.use_mocks:
            cloud_llm = CloudLLMClient()
            if cloud_llm.is_configured():
                self.llm_client: ILLMClient = cloud_llm
            else:
                self.llm_client = MockLLMClient()
        else:
            self.llm_client = MockLLMClient()


        # Input
        self.input_ctrl: IInputController = PynputHumanController(config=self.config.input)

    def create_feed_comment_use_case(self) -> FeedCommentUseCase:
        return FeedCommentUseCase(
            config=self.config,
            window_mgr=self.window_mgr,
            capture=self.screen_capture,
            card_segmenter=self.card_segmenter,
            anchor_detector=self.anchor_detector,
            ocr=self.ocr_recognizer,
            text_filter=self.text_filter,
            llm=self.llm_client,
            input_ctrl=self.input_ctrl,
            limiter=self.rate_limiter,
        )

    def create_thread_reply_use_case(self) -> ThreadReplyUseCase:
        return ThreadReplyUseCase(
            config=self.config,
            window_mgr=self.window_mgr,
            capture=self.screen_capture,
            comment_grouper=self.comment_grouper,
            ocr=self.ocr_recognizer,
            text_filter=self.text_filter,
            llm=self.llm_client,
            input_ctrl=self.input_ctrl,
            limiter=self.rate_limiter,
        )
