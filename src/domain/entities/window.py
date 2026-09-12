from dataclasses import dataclass
from src.domain.entities.geometry import BoundingBox


@dataclass(frozen=True)
class WindowInfo:
    hwnd: int
    title: str
    rect: BoundingBox
    is_active: bool = False
    is_minimized: bool = False
