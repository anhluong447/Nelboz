from typing import Any
from src.domain.ports.ocr import ITextRecognizer


class MockTextRecognizer(ITextRecognizer):
    """Mock OCR engine for pipeline verification before model training."""

    def __init__(self, default_text: str = "Bài viết chia sẻ kiến thức lập trình Python và AI thú vị."):
        self.default_text = default_text

    def recognize_text(self, image_crop: Any) -> str:
        return self.default_text
