import random
import time
from typing import Optional

try:
    from pynput.mouse import Controller as MouseController, Button
    from pynput.keyboard import Controller as KeyboardController, Key
except ImportError:
    MouseController = None
    KeyboardController = None
    Button = None
    Key = None

from src.config.settings import InputConfig
from src.domain.entities.geometry import Point
from src.domain.ports.input import IInputController
from src.infrastructure.input.bezier import generate_bezier_trajectory
from src.infrastructure.input.fail_safe import FailSafeManager, default_fail_safe


class PynputHumanController(IInputController):
    """Simulates realistic human mouse movement, key typing, and delay distributions with fail-safe support."""

    def __init__(
        self,
        config: Optional[InputConfig] = None,
        fail_safe: Optional[FailSafeManager] = None,
    ):
        self.config = config or InputConfig()
        self.fail_safe = fail_safe or default_fail_safe
        self.mouse = MouseController() if MouseController else None
        self.keyboard = KeyboardController() if KeyboardController else None

    def move_to(self, target: Point) -> None:
        if not self.mouse:
            return

        self.fail_safe.check()

        current_x, current_y = self.mouse.position
        start_pt = Point(x=int(current_x), y=int(current_y))

        # Target jitter: humans never hit the exact same pixel twice
        jitter_x = random.randint(-2, 2)
        jitter_y = random.randint(-2, 2)
        effective_target = Point(x=target.x + jitter_x, y=target.y + jitter_y)

        should_overshoot = random.random() < self.config.overshoot_chance
        trajectory = generate_bezier_trajectory(
            start=start_pt,
            end=effective_target,
            deviation_max=self.config.bezier_deviation_max,
            overshoot=should_overshoot,
        )

        for pt in trajectory:
            self.fail_safe.check()
            self.mouse.position = (pt.x, pt.y)
            # Sleep between 5ms to 18ms per trajectory step
            time.sleep(random.uniform(0.005, 0.018))

    def click(self, target: Optional[Point] = None) -> None:
        if not self.mouse:
            return

        self.fail_safe.check()

        if target:
            self.move_to(target)

        # Realistic pre-click hesitation
        time.sleep(random.uniform(0.06, 0.14))
        self.fail_safe.check()

        self.mouse.press(Button.left)
        # Mouse button held down duration (typically 50-130ms)
        time.sleep(random.uniform(0.05, 0.12))
        self.mouse.release(Button.left)
        time.sleep(random.uniform(0.08, 0.18))

    def type_text(self, text: str) -> None:
        if not self.keyboard:
            return

        self.fail_safe.check()

        # Estimate inter-key delay based on WPM
        wpm = random.uniform(self.config.typing_wpm_min, self.config.typing_wpm_max)
        avg_cps = (wpm * 5) / 60.0
        base_delay = 1.0 / max(1.0, avg_cps)

        for char in text:
            self.fail_safe.check()
            # Add stochastic variance (log-normal-ish feel)
            variance = random.uniform(0.65, 1.45)
            # Punctuation or space usually takes slightly longer
            if char in " ,.!?\n":
                variance *= random.uniform(1.3, 2.1)

            self.keyboard.type(char)
            time.sleep(base_delay * variance)

    def press_key(self, key_name: str) -> None:
        if not self.keyboard or not Key:
            return

        self.fail_safe.check()

        key_mapping = {
            "enter": Key.enter,
            "esc": Key.esc,
            "tab": Key.tab,
            "space": Key.space,
            "backspace": Key.backspace,
        }
        target_key = key_mapping.get(key_name.lower())
        if target_key:
            self.keyboard.press(target_key)
            time.sleep(random.uniform(0.05, 0.12))
            self.keyboard.release(target_key)

    def clear_input(self) -> None:
        """Selects all text and deletes it (Ctrl+A -> Backspace) to clean up draft text."""
        if not self.keyboard or not Key:
            return

        self.fail_safe.check()

        # Ctrl + A
        self.keyboard.press(Key.ctrl)
        time.sleep(random.uniform(0.04, 0.08))
        self.keyboard.press("a")
        time.sleep(random.uniform(0.04, 0.08))
        self.keyboard.release("a")
        self.keyboard.release(Key.ctrl)

        time.sleep(random.uniform(0.08, 0.15))
        self.fail_safe.check()

        # Backspace
        self.keyboard.press(Key.backspace)
        time.sleep(random.uniform(0.04, 0.08))
        self.keyboard.release(Key.backspace)

        time.sleep(random.uniform(0.08, 0.15))

    def scroll(self, clicks: int) -> None:
        if not self.mouse:
            return

        self.fail_safe.check()

        # Split scroll into variable small increments for smooth scrolling
        sign = 1 if clicks > 0 else -1
        remaining = abs(clicks)

        while remaining > 0:
            self.fail_safe.check()
            step = min(remaining, random.randint(1, 3))
            self.mouse.scroll(0, sign * step)
            remaining -= step
            time.sleep(random.uniform(0.06, 0.18))

    def sleep_random(self, min_sec: float, max_sec: float) -> None:
        mid = (min_sec + max_sec) / 2.0
        sigma = (max_sec - min_sec) / 4.0
        duration = random.gauss(mid, sigma)
        duration = max(min_sec, min(max_sec, duration))

        # Check fail-safe periodically during sleep
        step_sleep = 0.1
        elapsed = 0.0
        while elapsed < duration:
            self.fail_safe.check()
            chunk = min(step_sleep, duration - elapsed)
            time.sleep(chunk)
            elapsed += chunk
