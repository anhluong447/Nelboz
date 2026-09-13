import threading
from typing import Any, Optional

try:
    from pynput.keyboard import Listener as KeyboardListener, Key
    from pynput.mouse import Controller as MouseController
except ImportError:
    KeyboardListener = None
    Key = None
    MouseController = None


class EmergencyStopException(Exception):
    """Raised immediately when the user hits the kill switch (ESC or corner)."""
    pass


class FailSafeManager:
    """Monitors global input for emergency user intervention.

    Trigger conditions:
    1. Key.esc is pressed.
    2. Mouse cursor moves to the top-left corner (x <= 5 and y <= 5).
    """

    def __init__(self, check_corner: bool = True):
        self.check_corner = check_corner
        self._aborted = False
        self._listener: Optional[KeyboardListener] = None
        self._mouse = MouseController() if MouseController else None
        self._lock = threading.Lock()

    def start(self) -> "FailSafeManager":
        """Starts the background keyboard listener for the ESC key."""
        with self._lock:
            self._aborted = False
            if KeyboardListener and self._listener is None:
                self._listener = KeyboardListener(on_press=self._on_key_press)
                self._listener.daemon = True
                self._listener.start()
        return self

    def stop(self) -> None:
        """Stops the background keyboard listener."""
        with self._lock:
            if self._listener is not None:
                try:
                    self._listener.stop()
                except Exception:
                    pass
                self._listener = None

    def _on_key_press(self, key: Any) -> None:
        if Key and key == Key.esc:
            with self._lock:
                self._aborted = True

    @property
    def is_aborted(self) -> bool:
        with self._lock:
            if self._aborted:
                return True

        if self.check_corner and self._mouse:
            try:
                x, y = self._mouse.position
                if x <= 5 and y <= 5:
                    with self._lock:
                        self._aborted = True
                    return True
            except Exception:
                pass

        return False

    def check(self) -> None:
        """Raises EmergencyStopException if an abort condition has occurred."""
        if self.is_aborted:
            raise EmergencyStopException("Kill switch activated! Emergency stop triggered by user.")

    def reset(self) -> None:
        """Resets the aborted state."""
        with self._lock:
            self._aborted = False

    def __enter__(self) -> "FailSafeManager":
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()


# Global default instance
default_fail_safe = FailSafeManager()
