from abc import ABC, abstractmethod
from typing import Any


class ITextRecognizer(ABC):
    @abstractmethod
    def recognize_text(self, image_crop: Any) -> str:
        """Recognizes Vietnamese text from a cropped image of post/comment text area."""
        pass
