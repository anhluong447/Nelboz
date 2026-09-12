from abc import ABC, abstractmethod
from typing import Optional
from src.domain.entities.window import WindowInfo


class IWindowManager(ABC):
    @abstractmethod
    def find_target_window(self, title_pattern: str) -> Optional[WindowInfo]:
        """Finds window matching regex title pattern."""
        pass

    @abstractmethod
    def is_window_active(self, hwnd: int) -> bool:
        """Checks if window with hwnd is currently active / foreground."""
        pass

    @abstractmethod
    def focus_window(self, hwnd: int) -> bool:
        """Brings the window to foreground if needed."""
        pass
