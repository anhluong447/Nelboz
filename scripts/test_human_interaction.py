import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.domain.entities.geometry import Point
from src.infrastructure.input.fail_safe import default_fail_safe, EmergencyStopException
from src.infrastructure.input.pynput_controller import PynputHumanController


def main():
    print("=" * 65)
    print("HUMAN-LIKE INPUT INTERACTION TEST BENCH")
    print("=" * 65)
    print("Notice: Press [ESC] at ANY time to abort via Emergency Kill Switch.")
    print("You have 3 seconds to place your mouse and observe...")
    print("=" * 65)

    controller = PynputHumanController()

    with default_fail_safe:
        try:
            for i in range(3, 0, -1):
                print(f"Starting in {i}s...")
                time.sleep(1)

            print("\n[Test 1/4] Moving mouse via Cubic Bézier curve...")
            target1 = Point(700, 400)
            print(f" -> Moving to Point({target1.x}, {target1.y})")
            controller.move_to(target1)
            controller.sleep_random(0.5, 1.0)

            target2 = Point(950, 650)
            print(f" -> Moving to Point({target2.x}, {target2.y}) with natural curve")
            controller.move_to(target2)
            controller.sleep_random(0.5, 1.0)

            print("\n[Test 2/4] Natural click test (realistic down/up delay)...")
            controller.click(Point(950, 650))
            print(" -> Clicked successfully.")

            print("\n[Test 3/4] Typing simulation test...")
            sample_text = "Test human-like typing simulation..."
            print(f" -> Typing draft: '{sample_text}'")
            controller.type_text(sample_text)
            print(" -> Finished typing. Pausing 1.5s...")
            controller.sleep_random(1.2, 1.8)

            print("\n[Test 4/4] Clearing typed text (Ctrl+A -> Backspace)...")
            controller.clear_input()
            print(" -> Cleared input field safely.")

            print("\n[Optional] Smooth scroll demonstration...")
            print(" -> Scrolling down 2 steps smoothly...")
            controller.scroll(-2)
            controller.sleep_random(0.5, 1.0)

            print("\n" + "=" * 65)
            print("ALL INTERACTION TESTS COMPLETED SUCCESSFULLY!")
            print("=" * 65)

        except EmergencyStopException:
            print("\n[EMERGENCY STOP TRIGGERED] Aborted immediately by user [ESC]!")
            sys.exit(0)


if __name__ == "__main__":
    main()
