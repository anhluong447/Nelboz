from typing import Any, Optional
from src.domain.ports.ocr import ITextRecognizer


class CrnnTextRecognizer(ITextRecognizer):
    """Custom PyTorch lightweight CRNN (CNN + BiLSTM + CTC) text recognizer for Vietnamese."""

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self._model = None
        # Model loading will be connected in Phase 3 after training

    def recognize_text(self, image_crop: Any) -> str:
        if self._model is None:
            # Fallback until weights are loaded
            return ""
        return ""
