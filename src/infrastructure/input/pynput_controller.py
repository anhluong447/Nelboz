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


class PynputHumanController(IInputController):
    """Simulates realistic human mouse movement, key typing, and delay distributions."""

    def __init__(self, config: Optional[InputConfig] = None):
        self.config = config or InputConfig()
        self.mouse = MouseController() if MouseController else None
        self.keyboard = KeyboardController() if KeyboardController else None

    def move_to(self, target: Point) -> None:
        if not self.mouse:
            return

        current_x, current_y = self.mouse.position
        start_pt = Point(x=int(current_x), y=int(current_y))

        should_overshoot = random.random() < self.config.overshoot_chance
        trajectory = generate_bezier_trajectory(
            start=start_pt,
            end=target,
            deviation_max=self.config.bezier_deviation_max,
            overshoot=should_overshoot,
        )

        for pt in trajectory:
            self.mouse.position = (pt.x, pt.y)
            # Sleep between 5ms to 18ms per trajectory step
            time.sleep(random.uniform(0.005, 0.018))

    def click(self, target: Optional[Point] = None) -> None:
        if not self.mouse:
            return

        if target:
            self.move_to(target)

        # Realistic pre-click pause
        time.sleep(random.uniform(0.05, 0.12))
        self.mouse.press(Button.left)
        # Mouse button held down duration (typically 50-130ms)
        time.sleep(random.uniform(0.06, 0.14))
        self.mouse.release(Button.left)
        time.sleep(random.uniform(0.08, 0.18))

    def type_text(self, text: str) -> None:
        if not self.keyboard:
            return

        # Estimate inter-key delay based on WPM
        wpm = random.uniform(self.config.typing_wpm_min, self.config.typing_wpm_max)
        avg_cps = (wpm * 5) / 60.0
        base_delay = 1.0 / max(1.0, avg_cps)

        for char in text:
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

    def scroll(self, clicks: int) -> None:
        if not self.mouse:
            return

        # Split scroll into variable small increments
        sign = 1 if clicks > 0 else -1
        remaining = abs(clicks)

        while remaining > 0:
            step = min(remaining, random.randint(1, 3))
            self.mouse.scroll(0, sign * step)
            remaining -= step
            time.sleep(random.uniform(0.08, 0.22))

    def sleep_random(self, min_sec: float, max_sec: float) -> None:
        # Gaussian distribution centered around average
        mid = (min_sec + max_sec) / 2.0
        sigma = (max_sec - min_sec) / 4.0
        duration = random.gauss(mid, sigma)
        duration = max(min_sec, min(max_sec, duration))
        time.sleep(duration)
