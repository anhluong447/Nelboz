from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Point:
    x: int
    y: int

    def offset(self, dx: int, dy: int) -> "Point":
        return Point(x=self.x + dx, y=self.y + dy)

    def to_tuple(self) -> Tuple[int, int]:
        return (self.x, self.y)


@dataclass(frozen=True)
class BoundingBox:
    x: int
    y: int
    width: int
    height: int

    @property
    def left(self) -> int:
        return self.x

    @property
    def top(self) -> int:
        return self.y

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height

    @property
    def center(self) -> Point:
        return Point(x=self.x + self.width // 2, y=self.y + self.height // 2)

    def contains(self, point: Point) -> bool:
        return (self.left <= point.x <= self.right) and (self.top <= point.y <= self.bottom)

    def intersects(self, other: "BoundingBox") -> bool:
        return not (
            self.right < other.left
            or self.left > other.right
            or self.bottom < other.top
            or self.top > other.bottom
        )

    def offset(self, dx: int, dy: int) -> "BoundingBox":
        return BoundingBox(x=self.x + dx, y=self.y + dy, width=self.width, height=self.height)

    def to_tuple(self) -> Tuple[int, int, int, int]:
        """Returns (x, y, width, height)."""
        return (self.x, self.y, self.width, self.height)

    def to_ltrb(self) -> Tuple[int, int, int, int]:
        """Returns (left, top, right, bottom)."""
        return (self.left, self.top, self.right, self.bottom)
