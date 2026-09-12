from typing import Any, Optional
import numpy as np

try:
    import mss
except ImportError:
    mss = None

from src.domain.entities.geometry import BoundingBox
from src.domain.entities.window import WindowInfo
from src.domain.ports.capture import IScreenCapture


class MssScreenCapture(IScreenCapture):
    """Captures screen regions and active windows using mss library."""

    def __init__(self):
        self._sct = mss.mss() if mss else None

    def capture_region(self, region: BoundingBox) -> Optional[np.ndarray]:
        if not self._sct:
            return None

        monitor = {
            "left": region.x,
            "top": region.y,
            "width": max(1, region.width),
            "height": max(1, region.height),
        }
        sct_img = self._sct.grab(monitor)
        # Convert BGRA to BGR numpy array
        img_np = np.array(sct_img)
        if img_np.shape[2] == 4:
            return img_np[:, :, :3]
        return img_np

    def capture_window(self, window: WindowInfo) -> Optional[np.ndarray]:
        return self.capture_region(window.rect)
