import argparse
import ctypes
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

# Ensure DPI Awareness is set immediately before any GUI / coordinate queries
try:
    # 2 = PROCESS_PER_MONITOR_DPI_AWARE
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.infrastructure.window.win32_window_manager import Win32WindowManager
from src.infrastructure.capture.mss_screen_capture import MssScreenCapture
from src.domain.entities.geometry import BoundingBox

try:
    import cv2
except ImportError:
    cv2 = None

try:
    from pynput import keyboard
except ImportError:
    keyboard = None


def get_unique_filename(output_dir: Path, prefix: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    counter = 1
    while True:
        candidate = output_dir / f"{prefix}_{timestamp}_{counter:03d}.png"
        if not candidate.exists():
            return candidate
        counter += 1


class SampleCapturer:
    def __init__(self, mode: str = "feed", title_pattern: str = ".*Chrome.*"):
        self.mode = mode
        self.title_pattern = title_pattern
        self.window_mgr = Win32WindowManager(dpi_aware=True)
        self.capture = MssScreenCapture()
        self.output_dir = PROJECT_ROOT / "data" / "raw_samples" / self.mode
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.capture_count = 0

    def capture_once(self) -> bool:
        target_win = self.window_mgr.find_target_window(self.title_pattern)
        if not target_win:
            print(f"[!] Khong tim thay cua so phu hop voi pattern: '{self.title_pattern}'")
            return False

        rect = target_win.rect
        print(f"[*] Muc tieu: '{target_win.title[:45]}...' | Rect: {rect.width}x{rect.height} tai ({rect.x}, {rect.y})")

        img = self.capture.capture_window(target_win)
        if img is None or img.size == 0:
            print("[!] Loi: Khong capture duoc hinh anh.")
            return False

        file_path = get_unique_filename(self.output_dir, self.mode)
        if cv2 is not None:
            cv2.imwrite(str(file_path), img)
        else:
            # Fallback if cv2 not loaded
            import numpy as np
            from PIL import Image
            rgb = img[:, :, ::-1] # BGR to RGB
            Image.fromarray(rgb).save(file_path)

        self.capture_count += 1
        print(f"[+] [{self.capture_count}] Da luu anh: {file_path.name} ({img.shape[1]}x{img.shape[0]} px)")
        # Beep notification on Windows
        try:
            ctypes.windll.kernel32.Beep(1000, 150)
        except Exception:
            pass
        return True

    def run_hotkey_listener(self) -> None:
        """Listens for F8 hotkey in background so you can browse Chrome and capture instantly without alt-tabbing."""
        if not keyboard:
            print("[!] Thư viện pynput chưa sẵn sàng, chuyển sang chế độ gõ phím Enter tại terminal.")
            self.run_interactive_terminal()
            return

        print("\n" + "=" * 65)
        print(f"  AUTO SAMPLE CAPTURE TOOL — Mode: [{self.mode.upper()}]")
        print("=" * 65)
        print(f"[*] Thu muc luu: data/raw_samples/{self.mode}/")
        print("[*] Huong dan su dung:")
        print("    -> Mo Chrome lướt Facebook bình thường (không cần chuyển qua lại terminal).")
        print("    -> Nhan phim [F8] bat cu luc nao de chup anh viewport Chrome.")
        print("    -> Nhan [ESC] hoac [Ctrl + C] tai day de dung script.")
        print("=" * 65 + "\n")

        def on_press(key):
            try:
                if key == keyboard.Key.f8:
                    self.capture_once()
                elif key == keyboard.Key.esc:
                    print("\n[*] Nhan ESC. Ket thuc qua trinh capture.")
                    return False
            except Exception as e:
                print(f"[!] Loi: {e}")

        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()

    def run_interactive_terminal(self) -> None:
        print("\n" + "=" * 65)
        print(f"  TERMINAL CAPTURE MODE — Mode: [{self.mode.upper()}]")
        print("=" * 65)
        print("[*] Nhan [Enter] de chup 1 frame viewport cua Chrome.")
        print("[*] Go 'q' roi Enter de thoat.")
        print("=" * 65 + "\n")

        while True:
            cmd = input(">> Nhan Enter de capture (q de thoat): ").strip()
            if cmd.lower() == 'q':
                break
            self.capture_once()


def main():
    parser = argparse.ArgumentParser(description="Facebook Sample Capture Tool")
    parser.add_argument(
        "--mode",
        choices=["feed", "threads"],
        default="feed",
        help="Capture mode: 'feed' for post cards, 'threads' for comment threads",
    )
    parser.add_argument(
        "--title",
        default=".*Chrome.*",
        help="Window title regex pattern (default: '.*Chrome.*')",
    )
    parser.add_argument(
        "--terminal",
        action="store_true",
        help="Force terminal Enter key instead of F8 global hotkey",
    )
    args = parser.parse_args()

    capturer = SampleCapturer(mode=args.mode, title_pattern=args.title)
    if args.terminal or not keyboard:
        capturer.run_interactive_terminal()
    else:
        capturer.run_hotkey_listener()


if __name__ == "__main__":
    main()
