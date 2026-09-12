import re
import ctypes
from typing import Optional, List, Tuple
from src.domain.entities.geometry import BoundingBox
from src.domain.entities.window import WindowInfo
from src.domain.ports.window import IWindowManager

try:
    import win32gui
    import win32process
    import win32con
except ImportError:
    win32gui = None
    win32process = None
    win32con = None


class Win32WindowManager(IWindowManager):
    """Manages Chrome window detection, focus, and viewport geometry using Win32 API."""

    def __init__(self, dpi_aware: bool = True):
        self.dpi_aware = dpi_aware
        if self.dpi_aware:
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI aware
            except Exception:
                try:
                    ctypes.windll.user32.SetProcessDPIAware()
                except Exception:
                    pass

    def find_target_window(self, title_pattern: str) -> Optional[WindowInfo]:
        regex = re.compile(title_pattern, re.IGNORECASE)
        found_windows: List[Tuple[int, str]] = []

        def enum_windows_callback(hwnd: int, extra: None) -> bool:
            if not win32gui or not win32gui.IsWindowVisible(hwnd):
                return True
            title = win32gui.GetWindowText(hwnd)
            if regex.search(title):
                found_windows.append((hwnd, title))
            return True

        if win32gui:
            win32gui.EnumWindows(enum_windows_callback, None)

        if not found_windows:
            return None

        # Pick the first matching visible window
        hwnd, title = found_windows[0]
        rect = self._get_window_rect(hwnd)
        is_active = self.is_window_active(hwnd)
        is_min = win32gui.IsIconic(hwnd) if win32gui else False

        return WindowInfo(
            hwnd=hwnd,
            title=title,
            rect=rect,
            is_active=is_active,
            is_minimized=bool(is_min),
        )

    def is_window_active(self, hwnd: int) -> bool:
        if not win32gui:
            return False
        return win32gui.GetForegroundWindow() == hwnd

    def focus_window(self, hwnd: int) -> bool:
        if not win32gui:
            return False
        try:
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            return True
        except Exception:
            return False

    def _get_window_rect(self, hwnd: int) -> BoundingBox:
        if not win32gui:
            return BoundingBox(x=0, y=0, width=1920, height=1080)
        # Using DwmGetWindowAttribute for accurate borderless rect if possible
        try:
            rect = ctypes.wintypes.RECT()
            dwm = ctypes.windll.dwmapi
            # DWMWA_EXTENDED_FRAME_BOUNDS = 9
            result = dwm.DwmGetWindowAttribute(
                ctypes.wintypes.HWND(hwnd),
                ctypes.wintypes.DWORD(9),
                ctypes.byref(rect),
                ctypes.sizeof(rect),
            )
            if result == 0:
                return BoundingBox(
                    x=rect.left,
                    y=rect.top,
                    width=rect.right - rect.left,
                    height=rect.bottom - rect.top,
                )
        except Exception:
            pass

        # Fallback to GetWindowRect
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        return BoundingBox(x=left, y=top, width=right - left, height=bottom - top)
