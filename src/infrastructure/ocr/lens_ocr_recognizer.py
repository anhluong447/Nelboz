import json
import logging
import subprocess
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
import cv2
import numpy as np
from src.domain.ports.ocr import ITextRecognizer

logger = logging.getLogger(__name__)


class LensOcrRecognizer(ITextRecognizer):
    """Adapter for Google Chrome Lens OCR via external Node.js script (lens_ocr.js).

    Provides highly accurate Vietnamese OCR (including slang, diacritics, and teen-code)
    without running heavy deep-learning models locally.
    """

    DEFAULT_SCRIPT_PATH = Path(__file__).resolve().parent.parent.parent.parent / "ocr" / "lens_ocr.js"
    DEFAULT_TEMP_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "temp_ocr"

    def __init__(
        self,
        script_path: Optional[Path] = None,
        node_executable: str = "node",
        temp_dir: Optional[Path] = None,
        timeout_sec: float = 20.0,
    ):
        self.script_path = Path(script_path) if script_path else self.DEFAULT_SCRIPT_PATH
        self.node_executable = node_executable
        self.temp_dir = Path(temp_dir) if temp_dir else self.DEFAULT_TEMP_DIR
        self.timeout_sec = timeout_sec

        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def is_available(self) -> bool:
        """Checks if Node.js and the lens_ocr.js script are both accessible."""
        if not self.script_path.exists():
            return False
        try:
            res = subprocess.run(
                [self.node_executable, "-v"],
                capture_output=True,
                text=True,
                timeout=5.0,
            )
            return res.returncode == 0
        except Exception:
            return False

    def recognize_text(self, image: Any) -> str:
        """Extracts text from an image (numpy array or file path).

        Args:
            image: BGR/Grayscale np.ndarray or str/Path to image file.

        Returns:
            Extracted text string (concatenated in reading order).
        """
        result = self.recognize_with_segments(image)
        return result.get("full_text", "")

    def recognize_with_segments(self, image: Any) -> Dict[str, Any]:
        """Extracts text along with detailed word/line bounding boxes.

        Args:
            image: BGR/Grayscale np.ndarray or str/Path to image file.

        Returns:
            Dict containing 'full_text' (str) and 'segments' (List[Dict]).
        """
        empty_res = {"full_text": "", "segments": []}
        if image is None:
            return empty_res

        # Case 1: image is already a path
        if isinstance(image, (str, Path)):
            img_path = Path(image)
            if not img_path.exists():
                logger.warning("Image path does not exist: %s", img_path)
                return empty_res
            return self._run_lens_cli(img_path)

        # Case 2: image is a numpy array
        if isinstance(image, np.ndarray):
            if image.size == 0 or image.shape[0] < 5 or image.shape[1] < 5:
                return empty_res

            temp_filename = f"ocr_{uuid.uuid4().hex[:8]}.png"
            temp_file_path = self.temp_dir / temp_filename
            try:
                cv2.imwrite(str(temp_file_path), image)
                return self._run_lens_cli(temp_file_path)
            finally:
                if temp_file_path.exists():
                    try:
                        temp_file_path.unlink()
                    except Exception as e:
                        logger.debug("Failed to remove temp OCR image: %s", e)

        return empty_res

    def _run_lens_cli(self, file_path: Path) -> Dict[str, Any]:
        """Invokes node lens_ocr.js and parses the output JSON."""
        empty_res = {"full_text": "", "segments": []}
        if not self.script_path.exists():
            logger.error("Lens OCR script not found at %s", self.script_path)
            return empty_res

        abs_file_path = Path(file_path).resolve()
        if not abs_file_path.exists():
            logger.warning("Image path does not exist: %s", abs_file_path)
            return empty_res

        try:
            cmd = [
                self.node_executable,
                str(self.script_path.resolve()),
                str(abs_file_path),
            ]

            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=self.timeout_sec,
                cwd=str(self.script_path.parent),
            )

            if proc.returncode != 0:
                logger.warning("Lens OCR process exited with code %d: %s", proc.returncode, proc.stderr.strip())
                return empty_res

            output_str = proc.stdout.strip()
            if not output_str:
                return empty_res

            data = json.loads(output_str)
            return data

        except subprocess.TimeoutExpired:
            logger.warning("Lens OCR call timed out after %.1f seconds.", self.timeout_sec)
            return empty_res
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse Lens OCR JSON: %s (Raw: %s)", e, proc.stdout[:200])
            return empty_res
        except Exception as e:
            logger.error("Unexpected error in Lens OCR: %s", e)
            return empty_res
