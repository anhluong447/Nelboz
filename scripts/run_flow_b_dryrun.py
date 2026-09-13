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
from src.domain.entities.geometry import Point
from src.domain.entities.decision import ActionType
from src.infrastructure.window.win32_window_manager import Win32WindowManager
from src.infrastructure.capture.mss_screen_capture import MssScreenCapture
from src.infrastructure.vision.anchor_detector import AnchorDetector
from src.infrastructure.vision.feed_card_segmenter import FeedCardSegmenter
from src.infrastructure.vision.comment_grouper import CommentThreadGrouper
from src.infrastructure.vision.expand_reply_detector import ExpandReplyDetector
from src.infrastructure.ocr.lens_ocr_recognizer import LensOcrRecognizer
from src.infrastructure.llm.cloud_llm_client import CloudLLMClient
from src.infrastructure.input.pynput_controller import PynputHumanController
from src.infrastructure.input.fail_safe import default_fail_safe, EmergencyStopException


def run_flow_b_dryrun():
    print("=" * 70)
    print("FACEBOOK AUTO-BOT — FLOW B (OPTION 2) DRY-RUN LIVE BENCHMARK")
    print("Comment Thread Reply with Expand Replies ('Xem x câu trả lời')")
    print("=" * 70)
    print("Safety Rules:")
    print("  1. Press [ESC] at ANY time to abort immediately via Emergency Kill Switch.")
    print("  2. In Dry-Run mode, the bot NEVER presses Enter (does not submit comments).")
    print("  3. The bot types draft text, pauses 2.5s for you to inspect, then deletes it.")
    print("=" * 70)

    window_mgr = Win32WindowManager(dpi_aware=True)
    capture = MssScreenCapture()
    feed_detector = AnchorDetector()
    grouper = CommentThreadGrouper(indent_threshold_px=75)
    expand_detector = ExpandReplyDetector()
    ocr = LensOcrRecognizer()
    llm = CloudLLMClient()
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

    # Center viewport point for scrolling
    center_screen = Point(target_win.rect.x + 900, target_win.rect.y + 500)
    input_ctrl.move_to(center_screen)
    input_ctrl.sleep_random(0.2, 0.4)

    # Expected column bounds for Facebook content (News Feed or Modal)
    # Typically X in [590, 1270]
    content_x1 = 590
    content_x2 = 1270

    max_scroll_attempts = 10
    target_comment = None

    with default_fail_safe:
        try:
            for attempt in range(1, max_scroll_attempts + 1):
                print(f"\n--- [Scan Attempt {attempt}/{max_scroll_attempts}] ---")
                print("Capturing viewport...")
                win_img = capture.capture_window(target_win)
                if win_img is None:
                    print("[ERROR] Failed to capture window image.")
                    return

                wh, ww = win_img.shape[:2]
                cv2.imwrite("data/flow_b_debug_full.png", win_img)

                # Crop content column
                crop_x1 = min(content_x1, ww - 100)
                crop_x2 = min(content_x2, ww)
                content_crop = win_img[:, crop_x1:crop_x2]
                cv2.imwrite("data/flow_b_debug_crop.png", content_crop)

                # Step 1: Check if comments are currently visible
                comments = grouper.group_comments(content_crop)
                l1_count = sum(1 for c in comments if c.level == 1)
                l2_count = sum(1 for c in comments if c.level == 2)

                # Also check for expand buttons ("Xem x câu trả lời" / "Xem x phản hồi")
                expand_buttons = expand_detector.detect_expand_buttons(content_crop)

                print(f" -> Visible comments: {len(comments)} (L1: {l1_count}, L2: {l2_count}) | Expand buttons: {len(expand_buttons)}")

                # If no comments or expand buttons visible, check if we need to open comments of a feed post first
                if len(comments) == 0 and len(expand_buttons) == 0:
                    print(" [!] No comments or expand buttons visible.")
                    print(" -> Checking if there is a post action bar to open comments...")
                    feed_anchors = feed_detector.detect_feed_anchors(win_img)
                    if feed_anchors:
                        post_anchor = feed_anchors[0]
                        print(f" [+] Found post action bar at ({post_anchor.x}, {post_anchor.y})")
                        comment_click_pt = feed_detector.get_comment_button_center(post_anchor, win_img)
                        screen_open_pt = Point(
                            x=target_win.rect.x + comment_click_pt.x,
                            y=target_win.rect.y + comment_click_pt.y,
                        )
                        print(f" -> Clicking post Comment button at Screen Point({screen_open_pt.x}, {screen_open_pt.y}) to display comments...")
                        input_ctrl.move_to(screen_open_pt)
                        input_ctrl.sleep_random(0.2, 0.4)
                        input_ctrl.click(screen_open_pt)
                        input_ctrl.sleep_random(1.5, 2.0)

                        # Re-scan after opening comments
                        continue
                    else:
                        print(" -> No post action bar visible either. Scrolling down smoothly...")
                        input_ctrl.move_to(center_screen)
                        input_ctrl.scroll(-2)
                        input_ctrl.sleep_random(1.2, 1.6)
                        continue

                # Step 2: If expand buttons found ("Xem x câu trả lời / phản hồi"), click to expand nested replies drop box!
                if expand_buttons:
                    first_expand = expand_buttons[0]
                    screen_expand_pt = Point(
                        x=target_win.rect.x + crop_x1 + first_expand.x,
                        y=target_win.rect.y + first_expand.y,
                    )
                    print(f"\n[Step 2] Found 'Xem x câu trả lời' at Point({screen_expand_pt.x}, {screen_expand_pt.y})!")
                    print(" -> Moving mouse via Bézier curve to expand button...")
                    input_ctrl.move_to(screen_expand_pt)
                    input_ctrl.sleep_random(0.3, 0.5)

                    print(" -> Clicking to expand nested replies drop box...")
                    input_ctrl.click(screen_expand_pt)
                    input_ctrl.sleep_random(1.5, 2.0)

                    # Re-capture after expanding replies
                    print(" -> Re-capturing after expansion...")
                    win_img = capture.capture_window(target_win)
                    content_crop = win_img[:, crop_x1:crop_x2]
                    comments = grouper.group_comments(content_crop)
                    print(f" -> Comments after expansion: {len(comments)}")

                if comments:
                    # Prefer replying to a nested Level 2 reply if available, else first comment
                    target_comment = next((c for c in comments if c.level == 2), comments[0])
                    print(f" [+] Target comment confirmed: {target_comment.id} (Level {target_comment.level})")
                    break

                # Scroll down slightly if needed
                print(" -> Scrolling slightly to reveal comments...")
                input_ctrl.move_to(center_screen)
                input_ctrl.scroll(-2)
                input_ctrl.sleep_random(1.2, 1.6)

            if not target_comment or not target_comment.reply_button_box:
                print(f"\n[!] Could not locate a target comment after {max_scroll_attempts} attempts.")
                print(" -> Check 'data/flow_b_debug_crop.png' for inspection.")
                return

            # Step 3: Reply Target & OCR
            reply_center = target_comment.reply_button_box.center
            screen_reply_pt = Point(
                x=target_win.rect.x + crop_x1 + reply_center.x,
                y=target_win.rect.y + reply_center.y,
            )

            print(f"\n[Step 3] Reply Target Confirmed:")
            print(f" -> Comment: {target_comment.id} (Level {target_comment.level})")
            print(f" -> Reply Button Screen Coords: Point({screen_reply_pt.x}, {screen_reply_pt.y})")

            tb = target_comment.text_box
            comment_text = ""
            if tb and content_crop is not None:
                c_crop = content_crop[max(0, tb.y):min(content_crop.shape[0], tb.bottom), max(0, tb.x):min(content_crop.shape[1], tb.right)]
                if c_crop.shape[0] >= 10 and c_crop.shape[1] >= 10:
                    cv2.imwrite("data/flow_b_comment_crop.png", c_crop)
                    comment_text = ocr.recognize_text(c_crop)

            print(f"\n[Step 4] Google Lens OCR Reading Comment Text:")
            print(f" -> \"{comment_text[:140]}...\"" if len(comment_text) > 140 else f" -> \"{comment_text or '(Chữ quá ngắn hoặc ảnh)'}\"")

            print("\n[Step 5] Calling DeepSeek (OpenRouter) to evaluate and generate reply...")
            decision = llm.evaluate_and_generate(comment_text or "Bình luận thú vị", ActionType.REPLY)
            print(f" -> AI Decision: should_act = {decision.should_act} | reason = '{decision.reason}'")

            if not decision.should_act:
                print(" -> AI decided to skip this comment. Exiting dry-run...")
                return

            draft_reply = decision.text or "Chuẩn luôn, mình cũng đồng quan điểm với bạn!"

            # Step 6: Bézier Move & Click
            print("\n[Step 6] Moving mouse via Cubic Bézier curve to 'Trả lời' button...")
            input_ctrl.move_to(screen_reply_pt)
            input_ctrl.sleep_random(0.3, 0.6)

            print("[Step 7] Clicking 'Trả lời' button to activate reply input...")
            input_ctrl.click(screen_reply_pt)
            input_ctrl.sleep_random(1.0, 1.5)

            # Step 8: Type AI-Generated Reply
            print(f"\n[Step 8] Typing AI-generated reply: '{draft_reply}'...")
            input_ctrl.type_text(draft_reply)

            # Step 9: Observation Pause
            print("\n[Step 9] Observation pause: Waiting 2.5s for you to inspect the reply box...")
            input_ctrl.sleep_random(2.3, 2.8)

            # Step 10: Safe Cleanup (Ctrl+A -> Backspace)
            print("\n[Step 10] [DRY-RUN SAFEGUARD] Clearing input (Ctrl+A -> Backspace)...")

            input_ctrl.clear_input()
            input_ctrl.sleep_random(0.5, 0.8)
            print(" -> Cleaned up successfully! Zero comments were submitted.")

            print("\n" + "=" * 70)
            print("FLOW B (OPTION 2) DRY-RUN COMPLETED 100% SUCCESSFULLY WITH ZERO DISRUPTION!")
            print("=" * 70)

        except EmergencyStopException:
            print("\n[EMERGENCY STOP] Execution aborted immediately by user [ESC]!")
            sys.exit(0)


if __name__ == "__main__":
    run_flow_b_dryrun()
