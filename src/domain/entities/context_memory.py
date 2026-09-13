import re
from typing import List, Set


class PostContextMemory:
    """Accumulates and stitches text extracted across multiple scroll passes of a Facebook post.

    Handles deduplication of overlapping lines, filtering of UI noise
    (e.g., 'Thích', 'Bình luận', 'Chia sẻ', 'Viết bình luận...', timestamp fragments),
    and ordering content from top to bottom.
    """

    # Common Facebook UI noise patterns to filter out
    UI_NOISE_PATTERNS = [
        r"^(thích|bình luận|chia sẻ|gửi|like|comment|share)$",
        r"^viết bình luận.*",
        r"^bình luận dưới tên.*",
        r"^phù hợp nhất$",
        r"^xem thêm.*",
        r"^xem tất cả.*bình luận.*",
        r"^\d+\s*(lượt thích|bình luận|lượt chia sẻ|thích)$",
        r"^\d+([,.]\d+)?[kK]?\s*(thích|bình luận|chia sẻ)$",
        r"^nhấn enter để.*",
    ]

    def __init__(self) -> None:
        self._lines: List[str] = []
        self._seen_lines_normalized: Set[str] = set()

    def add_ocr_result(self, raw_text: str) -> int:
        """Processes a raw OCR string from a scan pass and appends new unique lines.

        Args:
            raw_text: Full text returned by OCR engine.

        Returns:
            Count of newly added lines.
        """
        if not raw_text or not raw_text.strip():
            return 0

        added_count = 0
        raw_lines = raw_text.splitlines()

        for line in raw_lines:
            line_clean = line.strip()
            if not line_clean or len(line_clean) < 2:
                continue

            if self._is_ui_noise(line_clean):
                continue

            norm = self._normalize_line(line_clean)
            if norm in self._seen_lines_normalized:
                continue

            # Check for partial containment in previously seen longer lines
            if any(norm in seen for seen in self._seen_lines_normalized if len(seen) > len(norm) + 5):
                continue

            self._seen_lines_normalized.add(norm)
            self._lines.append(line_clean)
            added_count += 1

        return added_count

    def _normalize_line(self, line: str) -> str:
        """Normalizes a line for fuzzy matching: lowercase, alphanumeric and spaces only."""
        cleaned = re.sub(r"[^\w\s]", "", line.lower(), flags=re.UNICODE)
        return " ".join(cleaned.split())

    def _is_ui_noise(self, line: str) -> bool:
        """Determines if a line is a known Facebook UI button/stat."""
        line_lower = line.strip().lower()
        for pat in self.UI_NOISE_PATTERNS:
            if re.match(pat, line_lower, re.IGNORECASE):
                return True
        return False

    def get_full_context(self) -> str:
        """Returns the full accumulated post text joined by newlines."""
        return "\n".join(self._lines).strip()

    @property
    def line_count(self) -> int:
        return len(self._lines)

    @property
    def total_length(self) -> int:
        return sum(len(line) for line in self._lines)

    def is_sufficient(self, min_length: int = 15) -> bool:
        """Checks if accumulated text has enough substance for evaluation."""
        return self.total_length >= min_length

    def clear(self) -> None:
        """Resets the memory for a new post."""
        self._lines.clear()
        self._seen_lines_normalized.clear()
