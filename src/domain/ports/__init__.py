from src.domain.ports.window import IWindowManager
from src.domain.ports.capture import IScreenCapture
from src.domain.ports.vision import ICardSegmenter, IAnchorDetector, ICommentGrouper
from src.domain.ports.ocr import ITextRecognizer
from src.domain.ports.filter import ITextFilter
from src.domain.ports.llm import ILLMClient
from src.domain.ports.input import IInputController
from src.domain.ports.limiter import IRateLimiter

__all__ = [
    "IWindowManager",
    "IScreenCapture",
    "ICardSegmenter",
    "IAnchorDetector",
    "ICommentGrouper",
    "ITextRecognizer",
    "ITextFilter",
    "ILLMClient",
    "IInputController",
    "IRateLimiter",
]
