import unittest
import time
from src.infrastructure.limiter.sliding_rate_limiter import SlidingRateLimiter


class TestRateLimiter(unittest.TestCase):
    def test_rate_limiter_max_count(self):
        limiter = SlidingRateLimiter(
            window_seconds=60,
            limits={"test_action": 2},
            min_intervals={"test_action": 0.0},
        )

        self.assertTrue(limiter.can_perform("test_action"))
        limiter.record_action("test_action")

        self.assertTrue(limiter.can_perform("test_action"))
        limiter.record_action("test_action")

        # Limit reached (2 actions)
        self.assertFalse(limiter.can_perform("test_action"))

    def test_rate_limiter_min_interval(self):
        limiter = SlidingRateLimiter(
            window_seconds=60,
            limits={"test_action": 10},
            min_intervals={"test_action": 0.2},
        )

        self.assertTrue(limiter.can_perform("test_action"))
        limiter.record_action("test_action")

        # Immediately after, min interval is not met
        self.assertFalse(limiter.can_perform("test_action"))

        # After waiting min interval
        time.sleep(0.25)
        self.assertTrue(limiter.can_perform("test_action"))

