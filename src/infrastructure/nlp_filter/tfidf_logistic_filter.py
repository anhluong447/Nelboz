from typing import Optional
from src.domain.ports.filter import ITextFilter


class TfidfLogisticFilter(ITextFilter):
    """Fast pre-filter to discard ads, spam, or meaningless texts before calling LLM."""

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self._classifier = None
        self._vectorizer = None

    def should_process(self, text: str) -> bool:
        cleaned = text.strip()
        # Heuristic 1: Text must be at least 15 characters
        if len(cleaned) < 15:
            return False

        # Heuristic 2: Ignore typical ad / livestream spam words
        spam_keywords = ["mua ngay", "inbox giá", "giảm giá sốc", "link dưới cmt", "freeship"]
        text_lower = cleaned.lower()
        if any(kw in text_lower for kw in spam_keywords):
            return False

        # If trained model is present, run prediction
        if self._classifier and self._vectorizer:
            features = self._vectorizer.transform([cleaned])
            pred = self._classifier.predict(features)[0]
            return bool(pred == 1)

        return True
