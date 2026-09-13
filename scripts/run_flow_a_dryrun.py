import ctypes
import sys
import time
from pathlib import Path

# Ensure Per-Monitor DPI Awareness is set immediately before any GUI / coordinate queries
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import numpy as np
from src.config.settings import AppConfig
from src.domain.entities.geometry import Point
from src.infrastructure.window.win32_window_manager import Win32WindowManager
from src.infrastructure.capture.mss_screen_capture import MssScreenCapture
from src.infrastructure.vision.feed_card_segmenter import FeedCardSegmenter
from src.infrastructure.vision.anchor_detector import AnchorDetector
from src.infrastructure.input.pynput_controller import PynputHumanController
from src.infrastructure.input.fail_safe import default_fail_safe, EmergencyStopException


def run_dryrun():
    print("=" * 70)
    print("FACEBOOK AUTO-BOT — FLOW A DRY-RUN LIVE BENCHMARK")
    print("=" * 70)
    print("Safety Rules:")
    print("  1. Press [ESC] at ANY time to abort immediately via Emergency Kill Switch.")
    print("  2. In Dry-Run mode, the bot NEVER presses Enter (does not submit comments).")
    print("  3. The bot types draft text, pauses 2s for you to inspect, then deletes it.")
    print("=" * 70)

    window_mgr = Win32WindowManager(dpi_aware=True)
    capture = MssScreenCapture()
    segmenter = FeedCardSegmenter()
    detector = AnchorDetector()
    input_ctrl = PynputHumanController()

    target_win = window_mgr.find_target_window(".*(Cốc Cốc|Coc Coc|Chrome|Facebook).*")
    if not target_win:
        print("[ERROR] Cốc Cốc / Facebook window not found! Please open Facebook in Cốc Cốc.")
        return

    print(f"Found target window: '{target_win.title}' (Rect: {target_win.rect.to_tuple()})")
    print("Focusing Cốc Cốc in 2 seconds...")
    for i in range(2, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    window_mgr.focus_window(target_win.hwnd)
    time.sleep(0.8)

    # Move mouse inside Cốc Cốc feed area so wheel scrolls the browser, not the terminal
    feed_center = Point(target_win.rect.x + 900, target_win.rect.y + 500)
    input_ctrl.move_to(feed_center)
    input_ctrl.sleep_random(0.2, 0.4)

    max_scroll_attempts = 10
    target_anchor = None
    feed_img = None

    with default_fail_safe:
        try:
            for attempt in range(1, max_scroll_attempts + 1):
                print(f"\n--- [Scan Attempt {attempt}/{max_scroll_attempts}] ---")
                print("Capturing feed screenshot...")
                feed_img = capture.capture_window(target_win)
                if feed_img is None:
                    print("[ERROR] Failed to capture feed window image.")
                    return

                # Save debug image for inspection
                cv2.imwrite("data/dryrun_debug.png", feed_img)

                # Segment cards & detect action bars
                cards = segmenter.segment_cards(feed_img)
                anchors = detector.detect_feed_anchors(feed_img)

                # Inspect best raw template match score for diagnostics
                gray = cv2.cvtColor(feed_img, cv2.COLOR_BGR2GRAY)
                roi = gray[160:min(1080, gray.shape[0]), 590:min(680, gray.shape[1])]
                if roi.shape[0] >= 27 and roi.shape[1] >= 28 and detector._feed_like_tpl is not None:
                    res = cv2.matchTemplate(roi, detector._feed_like_tpl, cv2.TM_CCOEFF_NORMED)
                    _, max_score, _, max_loc = cv2.minMaxLoc(res)
                    print(f" -> Cards found: {len(cards)} | Action bars found: {len(anchors)}")
                    print(f" -> Best Like icon match: score={max_score:.3f} (Threshold: {detector.feed_like_threshold}) at ({max_loc[0]+590}, {max_loc[1]+160})")
                else:
                    print(f" -> Cards found: {len(cards)} | Action bars found: {len(anchors)}")

                if len(anchors) > 0:
                    target_anchor = anchors[0]
                    print(f" [+] Action bar successfully acquired at X={target_anchor.x}, Y={target_anchor.y}!")
                    break

                print(" [!] No action bar in current viewport (likely tall media).")
                print(" -> Scrolling down 2 steps smoothly (~180px)...")
                input_ctrl.move_to(feed_center)
                input_ctrl.scroll(-2)
                input_ctrl.sleep_random(1.2, 1.8)

            if not target_anchor:
                print(f"\n[!] Could not locate an action bar after {max_scroll_attempts} scroll attempts.")
                print(" -> Saved last capture to 'data/dryrun_debug.png' for inspection.")
                return

            comment_click_pt = detector.get_comment_button_center(target_anchor)

            # Convert to absolute screen coordinates
            screen_click_x = target_win.rect.x + comment_click_pt.x
            screen_click_y = target_win.rect.y + comment_click_pt.y
            target_pt = Point(x=screen_click_x, y=screen_click_y)

            print(f"\n[Step 3] Target confirmed:")
            print(f" -> Like Anchor at ({target_anchor.x}, {target_anchor.y})")
            print(f" -> Comment Button at screen coordinate: Point({target_pt.x}, {target_pt.y})")

            print("\n[Step 4] Moving mouse via Cubic Bézier curve...")
            input_ctrl.move_to(target_pt)
            input_ctrl.sleep_random(0.3, 0.6)

            print("[Step 5] Clicking Comment button to open comment input box...")
            input_ctrl.click(target_pt)
            input_ctrl.sleep_random(0.8, 1.4)

            sample_comment = "Chào bạn, bài viết chia sẻ rất hay và chi tiết!"
            print(f"\n[Step 6] Typing draft comment: '{sample_comment}'...")
            input_ctrl.type_text(sample_comment)

            print("\n[Step 7] Observation pause: Waiting 2.5s for you to inspect...")
            input_ctrl.sleep_random(2.0, 2.8)

            print("\n[Step 8] [DRY-RUN SAFEGUARD] Clearing comment input (Ctrl+A -> Backspace)...")
            input_ctrl.clear_input()
            input_ctrl.sleep_random(0.5, 1.0)
            print(" -> Cleaned up successfully! No comment was posted.")

            print("\n[Step 9] Smooth scrolling down to next post...")
            input_ctrl.move_to(feed_center)
            input_ctrl.scroll(-4)
            input_ctrl.sleep_random(1.0, 1.5)

            print("\n" + "=" * 70)
            print("DRY-RUN EXECUTION COMPLETED 100% SUCCESSFULLY WITH ZERO DISRUPTION!")
            print("=" * 70)

        except EmergencyStopException:
            print("\n[EMERGENCY STOP] Execution aborted immediately by user [ESC]!")
            sys.exit(0)


if __name__ == "__main__":
    run_dryrun()
