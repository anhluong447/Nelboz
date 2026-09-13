from pathlib import Path
import cv2
import numpy as np
import pytest
from src.infrastructure.ocr.lens_ocr_recognizer import LensOcrRecognizer


def test_lens_ocr_empty_or_none():
    recognizer = LensOcrRecognizer()
    assert recognizer.recognize_text(None) == ""
    assert recognizer.recognize_text(np.zeros((0, 0, 3), dtype=np.uint8)) == ""
    assert recognizer.recognize_text(np.zeros((4, 4, 3), dtype=np.uint8)) == ""
    assert recognizer.recognize_text("path/to/non_existent_file.png") == ""

    res = recognizer.recognize_with_segments(None)
    assert res == {"full_text": "", "segments": []}


def test_lens_ocr_availability():
    recognizer = LensOcrRecognizer()
    assert recognizer.is_available() is True


def test_lens_ocr_real_sample_crop():
    recognizer = LensOcrRecognizer()
    sample_path = Path("data/raw_samples/threads/crop_xem_phan_hoi.png")
    if not sample_path.exists():
        pytest.skip("Sample image not found")

    # Test passing path
    text_from_path = recognizer.recognize_text(sample_path)
    assert len(text_from_path) > 0
    assert "Chúng ta đều" in text_from_path or "Xem 1 phản hồi" in text_from_path

    # Test passing numpy array
    img = cv2.imread(str(sample_path))
    text_from_numpy = recognizer.recognize_text(img)
    assert len(text_from_numpy) > 0
    assert "Chúng ta đều" in text_from_numpy or "Xem 1 phản hồi" in text_from_numpy

    # Test segments output
    data = recognizer.recognize_with_segments(img)
    assert "full_text" in data
    assert "segments" in data
    assert len(data["segments"]) > 0
    assert data["segments"][0]["box"] is not None
