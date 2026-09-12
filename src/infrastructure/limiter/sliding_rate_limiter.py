from collections import deque
from datetime import datetime, timedelta
import time
from typing import Dict
from src.domain.ports.limiter import IRateLimiter


class SlidingRateLimiter(IRateLimiter):
    """Tracks action frequency with a sliding time window and enforces minimum spacing between actions."""

    def __init__(
        self,
        window_seconds: int = 3600,
        limits: Dict[str, int] = None,
        min_intervals: Dict[str, float] = None,
    ):
        self.window_seconds = window_seconds
        # limits: e.g. {"flow_a_comment": 5, "flow_b_reply": 3}
        self.limits = limits or {}
        # min_intervals: e.g. {"flow_a_comment": 300.0, "flow_b_reply": 400.0}
        self.min_intervals = min_intervals or {}
        self._history: Dict[str, deque] = {}
        self._last_action_time: Dict[str, float] = {}

    def can_perform(self, action_key: str) -> bool:
        now = time.time()

        # Check minimum spacing
        min_interval = self.min_intervals.get(action_key, 0.0)
        last_time = self._last_action_time.get(action_key, 0.0)
        if now - last_time < min_interval:
            return False

        # Check max actions in window
        limit = self.limits.get(action_key)
        if limit is None:
            return True

        if action_key not in self._history:
            self._history[action_key] = deque()

        queue = self._history[action_key]
        # Purge items older than window
        cutoff = now - self.window_seconds
        while queue and queue[0] < cutoff:
            queue.popleft()

        return len(queue) < limit

    def record_action(self, action_key: str) -> None:
        now = time.time()
        if action_key not in self._history:
            self._history[action_key] = deque()

        self._history[action_key].append(now)
        self._last_action_time[action_key] = now

    def wait_if_needed(self, action_key: str) -> None:
        while not self.can_perform(action_key):
            time.sleep(5.0)
