from abc import ABC, abstractmethod


class ITextFilter(ABC):
    @abstractmethod
    def should_process(self, text: str) -> bool:
        """Lightweight pre-filter (TF-IDF + LogReg) to quickly discard spam/ads/empty text."""
        pass
