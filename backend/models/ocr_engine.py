"""
OCR Engine — EasyOCR (CPU, English)
Downscales frames before OCR to keep latency low.
"""

import logging
from typing import Any

import cv2
import numpy as np

log = logging.getLogger("assistive_vision.ocr")


class OCREngine:
    def __init__(self, languages: list[str] | None = None, min_conf: float = 0.40):
        import easyocr

        self._min_conf = min_conf
        self._reader = easyocr.Reader(languages or ["en"], gpu=False, verbose=False)
        log.info("EasyOCR ready (languages=%s)", languages or ["en"])

    def extract(self, frame: np.ndarray) -> list[str]:
        """Return list of unique uppercase text strings detected in frame."""
        try:
            # Downscale for speed: max dimension → 480 px
            h, w = frame.shape[:2]
            scale = min(1.0, 480.0 / max(h, w))
            small = cv2.resize(frame, (int(w * scale), int(h * scale))) if scale < 1.0 else frame

            results: list[Any] = self._reader.readtext(small, detail=1, paragraph=False)
            seen: set[str] = set()
            texts: list[str] = []
            for (_bbox, text, conf) in results:
                t = text.strip().upper()
                if t and conf >= self._min_conf and t not in seen:
                    seen.add(t)
                    texts.append(t)
            return texts
        except Exception as exc:
            log.warning("OCR error: %s", exc)
            return []
