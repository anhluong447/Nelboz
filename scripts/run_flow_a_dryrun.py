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

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import numpy as np
from src.config.settings import AppConfig
from src.domain.entities.geometry import Point
from src.domain.entities.decision import ActionType
from src.domain.entities.context_memory import PostContextMemory
from src.infrastructure.window.win32_window_manager import Win32WindowManager
from src.infrastructure.capture.mss_screen_capture import MssScreenCapture
from src.infrastructure.vision.feed_card_segmenter import FeedCardSegmenter
from src.infrastructure.vision.anchor_detector import AnchorDetector
from src.infrastructure.ocr.lens_ocr_recognizer import LensOcrRecognizer
from src.infrastructure.llm.cloud_llm_client import CloudLLMClient
from src.infrastructure.input.pynput_controller import PynputHumanController
from src.infrastructure.input.fail_safe import default_fail_safe, EmergencyStopException


def run_dryrun():
    print("=" * 70)
    print("FACEBOOK AUTO-BOT — FLOW A DRY-RUN (STANDARDIZED PIPELINE)")
    print("Lăn -> Thấy post -> Nhấn nút Comment -> Bung Xem thêm -> OCR bài -> AI Comment")
    print("=" * 70)
    print("Safety Rules:")
    print("  1. Press [ESC] at ANY time to abort immediately via Emergency Kill Switch.")
    print("  2. In Dry-Run mode, the bot NEVER presses Enter (does not submit comments).")
    print("  3. The bot types draft text, pauses 2.5s for you to inspect, then deletes it.")
    print("=" * 70)

    window_mgr = Win32WindowManager(dpi_aware=True)
    capture = MssScreenCapture()
    segmenter = FeedCardSegmenter()
    detector = AnchorDetector()
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

    # Move mouse inside Cốc Cốc feed area so wheel scrolls the browser, not the terminal
    feed_center = Point(target_win.rect.x + 900, target_win.rect.y + 500)
    input_ctrl.move_to(feed_center)
    input_ctrl.sleep_random(0.2, 0.4)

    max_scroll_attempts = 10
    target_anchor = None
    feed_img = None

    with default_fail_safe:
        try:
            # -------------------------------------------------------------
            # BƯỚC 1 & 2: LĂN FEED VÀ PHÁT HIỆN POST
            # -------------------------------------------------------------
            for attempt in range(1, max_scroll_attempts + 1):
                print(f"\n--- [Lăn Feed & Quét Post: Lần {attempt}/{max_scroll_attempts}] ---")
                feed_img = capture.capture_window(target_win)
                if feed_img is None:
                    print("[ERROR] Failed to capture feed window image.")
                    return

                cv2.imwrite("data/flow_a_debug_feed.png", feed_img)

                # Detect action bars on feed
                anchors = detector.detect_feed_anchors(feed_img)

                # Filter anchors that are in safe viewing area (Y in 280..950, avoiding browser header)
                valid_anchors = [a for a in anchors if 280 <= a.y <= 950]
                print(f" -> Total action bars: {len(anchors)} | Safe visible action bars: {len(valid_anchors)}")

                if len(valid_anchors) > 0:
                    target_anchor = valid_anchors[0]
                    print(f" [+] Post action bar acquired at ({target_anchor.x}, {target_anchor.y})!")
                    break

                print(" [!] No suitable post in view. Scrolling down 2 steps (~180px)...")
                input_ctrl.move_to(feed_center)
                input_ctrl.scroll(-2)
                input_ctrl.sleep_random(1.2, 1.6)

            if not target_anchor:
                print(f"\n[!] Could not find a suitable post after {max_scroll_attempts} attempts.")
                return

            # -------------------------------------------------------------
            # BƯỚC 3: NHẤN NÚT COMMENT TRÊN ACTION BAR
            # -------------------------------------------------------------
            comment_click_pt = detector.get_comment_button_center(target_anchor, feed_img)
            screen_comment_btn = Point(
                x=target_win.rect.x + comment_click_pt.x,
                y=target_win.rect.y + comment_click_pt.y,
            )

            print(f"\n[Bước 3] Nhấn nút Comment trên action bar tại Point({screen_comment_btn.x}, {screen_comment_btn.y})...")
            print(" -> Di chuyển chuột Bézier tới nút Comment...")
            input_ctrl.move_to(screen_comment_btn)
            input_ctrl.sleep_random(0.3, 0.5)

            print(" -> Click nút Comment để mở ô input...")
            input_ctrl.click(screen_comment_btn)
            input_ctrl.sleep_random(1.0, 1.4)

            # -------------------------------------------------------------
            # BƯỚC 4: QUÉT ĐA TẦNG (MULTI-PASS SCROLL) & TÍCH LŨY POST CONTEXT MEMORY
            # -------------------------------------------------------------
            print("\n[Bước 4] Đọc bài viết đa tầng bằng Google Lens OCR kết hợp PostContextMemory...")
            context_memory = PostContextMemory()

            # Tọa độ cuộn feed an toàn (giữa khung bài viết)
            post_x1 = max(0, target_anchor.x - 10)
            post_x2 = min(feed_img.shape[1], target_anchor.x + target_anchor.width + 10)
            scroll_center = Point(
                x=int(target_win.rect.x + (post_x1 + post_x2) / 2),
                y=int(target_win.rect.y + 450),
            )

            # --- Đợt 4.1: Cuộn LÊN ĐỈNH BÀI VIẾT (+3 nấc) để lấy tiêu đề & nội dung đầu ---
            print(" -> [Đợt 1] Cuộn lên đỉnh bài viết để tránh trôi khung nhìn...")
            input_ctrl.move_to(scroll_center)
            input_ctrl.scroll(3)
            input_ctrl.sleep_random(0.7, 1.0)

            feed_img = capture.capture_window(target_win)
            # Crop vùng đỉnh bài viết (Y: 185 -> 720)
            crop_top = feed_img[185:720, post_x1:post_x2]
            cv2.imwrite("data/flow_a_crop_top.png", crop_top)
            ocr_top = ocr.recognize_with_segments(crop_top)
            added_top = context_memory.add_ocr_result(ocr_top.get("full_text", ""))
            print(f" [+] Đợt 1 (Đỉnh bài): Thu thập được {added_top} dòng văn bản.")

            # Kiểm tra nút 'Xem thêm' ở đợt 1
            segments = ocr_top.get("segments", [])
            xem_them_seg = None
            for seg in segments:
                text_clean = seg.get("text", "").strip().lower()
                if "xem thêm" in text_clean or "xem thèm" in text_clean or "see more" in text_clean:
                    xem_them_seg = seg
                    break

            if xem_them_seg and xem_them_seg.get("box"):
                box = xem_them_seg["box"]
                cx = box["x"] + box["width"] / 2.0
                cy = box["y"] + box["height"] / 2.0
                screen_xem_them = Point(
                    x=int(target_win.rect.x + post_x1 + cx * crop_top.shape[1]),
                    y=int(target_win.rect.y + 185 + cy * crop_top.shape[0]),
                )
                print(f" [+] Phát hiện nút 'Xem thêm' tại Point({screen_xem_them.x}, {screen_xem_them.y})!")
                print(" -> Di chuột Bézier và click 'Xem thêm' để mở trọn vẹn thông tin bài viết...")
                input_ctrl.move_to(screen_xem_them)
                input_ctrl.sleep_random(0.2, 0.4)
                input_ctrl.click(screen_xem_them)
                input_ctrl.sleep_random(0.8, 1.2)

                # Chụp lại sau khi bung
                feed_img = capture.capture_window(target_win)
                crop_top = feed_img[185:720, post_x1:post_x2]
                cv2.imwrite("data/flow_a_crop_top.png", crop_top)
                ocr_top = ocr.recognize_with_segments(crop_top)
                context_memory.add_ocr_result(ocr_top.get("full_text", ""))

            # --- Đợt 4.2: Cuộn XUỐNG (-3 nấc) để quét tiếp thân bài & ảnh ---
            print(" -> [Đợt 2] Cuộn xuống quét tiếp thân bài viết & hình ảnh...")
            input_ctrl.move_to(scroll_center)
            input_ctrl.scroll(-3)
            input_ctrl.sleep_random(0.7, 1.0)

            feed_img = capture.capture_window(target_win)
            # Crop vùng thân/ảnh bài viết (Y: 220 -> 850)
            crop_mid = feed_img[220:850, post_x1:post_x2]
            cv2.imwrite("data/flow_a_crop_mid.png", crop_mid)
            ocr_mid = ocr.recognize_with_segments(crop_mid)
            added_mid = context_memory.add_ocr_result(ocr_mid.get("full_text", ""))
            print(f" [+] Đợt 2 (Thân/Ảnh bài): Thu thập thêm {added_mid} dòng mới.")

            # --- Đợt 4.3: Định vị lại Action Bar & Ô Comment Input ---
            print(" -> [Đợt 3] Định vị lại Action Bar và ô comment...")
            new_anchors = detector.detect_feed_anchors(feed_img)
            valid_new = [a for a in new_anchors if a.y >= 200]
            if not valid_new:
                # Nếu action bar còn nằm hơi thấp, cuộn nhẹ thêm 1 nấc
                input_ctrl.scroll(-1)
                input_ctrl.sleep_random(0.5, 0.7)
                feed_img = capture.capture_window(target_win)
                new_anchors = detector.detect_feed_anchors(feed_img)
                valid_new = [a for a in new_anchors if a.y >= 200]

            if valid_new:
                target_anchor = valid_new[0]

            # Full OCR text combining all passes
            full_post_text = context_memory.get_full_context()
            print(f"\n[Tổng Hợp PostContextMemory] Trọn vẹn nội dung bài viết ({context_memory.line_count} dòng, {len(full_post_text)} ký tự):")
            print(f"\"\"\"\n{full_post_text}\n\"\"\"")

            if not context_memory.is_sufficient(min_length=15):
                print("[!] Nội dung bài viết không đủ ngữ cảnh để bình luận. Cuộn tiếp...")
                input_ctrl.move_to(feed_center)
                input_ctrl.scroll(-3)
                return

            # -------------------------------------------------------------
            # BƯỚC 5: DEEPSEEK ĐỌC HIỂU & SINH COMMENT
            # -------------------------------------------------------------
            print("\n[Bước 5] Gọi DeepSeek (OpenRouter) đọc hiểu toàn bài và sinh comment...")
            decision = llm.evaluate_and_generate(full_post_text, ActionType.COMMENT)
            print(f" -> AI Decision: should_act = {decision.should_act} | reason = '{decision.reason}'")

            if not decision.should_act:
                print(f" -> Bỏ qua bài viết: {decision.reason}. Cuộn sang bài tiếp theo...")
                input_ctrl.move_to(feed_center)
                input_ctrl.scroll(-3)
                return

            comment_to_type = decision.text or "Bài viết chia sẻ góc nhìn rất hay ạ!"
            print(f" -> Nội dung comment sinh ra: \"{comment_to_type}\"")

            # -------------------------------------------------------------
            # BƯỚC 6: COMMENT VÀO BÀI VIẾT (GÕ VÀ SAFEGUARD DRY-RUN)
            # -------------------------------------------------------------
            print("\n[Bước 6] Định vị và lấy focus chuẩn xác vào ô comment...")
            comment_click_pt = detector.get_comment_button_center(target_anchor, feed_img)
            screen_comment_btn = Point(
                x=target_win.rect.x + comment_click_pt.x,
                y=target_win.rect.y + comment_click_pt.y,
            )
            input_ctrl.move_to(screen_comment_btn)
            input_ctrl.sleep_random(0.2, 0.4)
            input_ctrl.click(screen_comment_btn)
            input_ctrl.sleep_random(0.5, 0.8)

            print(f" -> Gõ comment vào ô input đã sẵn sàng...")
            input_ctrl.type_text(comment_to_type)

            print("\n[Bước 7] Dừng quan sát 2.5s để bạn kiểm tra vị trí con trỏ và nội dung comment...")
            input_ctrl.sleep_random(2.3, 2.8)

            print("\n[Bước 8] [DRY-RUN SAFEGUARD] Xóa sạch ô nhập (Ctrl+A -> Backspace)...")
            input_ctrl.clear_input()
            input_ctrl.sleep_random(0.5, 0.8)
            print(" -> Dọn dẹp sạch sẽ 100%! Không có bình luận nào bị gửi đi.")

            print("\n[Bước 9] Cuộn mượt tiếp sang bài viết tiếp theo...")
            input_ctrl.move_to(feed_center)
            input_ctrl.scroll(-3)
            input_ctrl.sleep_random(1.0, 1.5)

            print("\n" + "=" * 70)
            print("CHU TRÌNH TƯƠNG TÁC FEED HOÀN TẤT 100% THÀNH CÔNG!")
            print("=" * 70)

        except EmergencyStopException:
            print("\n[EMERGENCY STOP] Dừng khẩn cấp bởi người dùng [ESC]!")
            sys.exit(0)


if __name__ == "__main__":
    run_dryrun()
