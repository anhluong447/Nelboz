from abc import ABC, abstractmethod
from typing import Optional
from src.domain.entities.geometry import Point


class IInputController(ABC):
    @abstractmethod
    def move_to(self, target: Point) -> None:
        """Moves mouse smoothly using Bezier curves with natural jitter and overshoot."""
        pass

    @abstractmethod
    def click(self, target: Optional[Point] = None) -> None:
        """Clicks at target or current location with human-like down/up delay."""
        pass

    @abstractmethod
    def type_text(self, text: str) -> None:
        """Types text character by character with stochastic inter-key delays."""
        pass

    @abstractmethod
    def press_key(self, key_name: str) -> None:
        """Presses and releases a specific key (e.g. 'enter', 'esc')."""
        pass

    @abstractmethod
    def scroll(self, clicks: int) -> None:
        """Scrolls with smooth variable increments."""
        pass

    @abstractmethod
    def clear_input(self) -> None:
        """Clears text in current active field (e.g. Ctrl+A -> Backspace)."""
        pass

    @abstractmethod
    def sleep_random(self, min_sec: float, max_sec: float) -> None:
        """Pauses execution for a random duration sampled from a realistic distribution."""
        pass
