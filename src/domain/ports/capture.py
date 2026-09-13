from abc import ABC, abstractmethod
from typing import Any
from src.domain.entities.geometry import BoundingBox
from src.domain.entities.window import WindowInfo


class IScreenCapture(ABC):
    @abstractmethod
    def capture_region(self, region: BoundingBox) -> Any:
        """Captures a specific screen region as a numpy ndarray (RGB/BGR)."""
        pass

    @abstractmethod
    def capture_window(self, window: WindowInfo) -> Any:
        """Captures the visible viewport area of target window."""
        pass

    @abstractmethod
    def capture_fullscreen(self) -> Any:
        """Captures the primary monitor full screen."""
        pass

