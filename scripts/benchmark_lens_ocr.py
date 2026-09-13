import sys
import time
from pathlib import Path

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


import cv2
from src.infrastructure.ocr.lens_ocr_recognizer import LensOcrRecognizer



def run_benchmark():
    print("=" * 70)
    print("BENCHMARK GOOGLE CHROME LENS OCR ADAPTER")
    print("=" * 70)

    recognizer = LensOcrRecognizer()
    if not recognizer.is_available():
        print("[ERROR] LensOcrRecognizer is NOT available (check Node.js / lens_ocr.js).")
        return

    print("Status: LensOcrRecognizer is online and ready.")

    test_images = [
        ("Comment & Expand Row", Path("data/raw_samples/threads/crop_xem_phan_hoi.png")),
        ("Nested Replies (Teen-code)", Path("data/raw_samples/threads/slice_400.png")),
        ("Comment Strip Grid", Path("data/raw_samples/threads/strip_comments.png")),
    ]

    for label, img_path in test_images:
        print(f"\n--- [Test Case: {label}] ---")
        if not img_path.exists():
            print(f"File not found: {img_path}")
            continue

        img = cv2.imread(str(img_path))
        print(f"Image Path: {img_path} | Shape: {img.shape}")

        t0 = time.perf_counter()
        data = recognizer.recognize_with_segments(img)
        t1 = time.perf_counter()

        elapsed_s = t1 - t0
        full_text = data.get("full_text", "")
        segments = data.get("segments", [])

        print(f"Latency: {elapsed_s:.2f}s | Segments count: {len(segments)}")
        print(f"Full Text Extracted:\n{full_text}")
        if segments:
            print(f"First Segment: text='{segments[0].get('text')}', box={segments[0].get('box')}")

    print("\n" + "=" * 70)
    print("BENCHMARK COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_benchmark()
