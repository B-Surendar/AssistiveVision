"""
Object Detector — YOLOv8n (nano, CPU-only, ~6 MB)
Auto-downloads yolov8n.pt from Ultralytics on first run.
"""

import logging
from typing import Any

import numpy as np

log = logging.getLogger("assistive_vision.detector")

# COCO classes relevant to assistive navigation
TARGET_CLASSES: dict[int, str] = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
    9: "traffic light",
    11: "stop sign",
    15: "cat",
    16: "dog",
    24: "backpack",
    25: "umbrella",
    26: "handbag",
    28: "suitcase",
    39: "bottle",
    56: "chair",
    60: "dining table",
    62: "tv",
    63: "laptop",
    67: "cell phone",
    73: "book",
}


class ObjectDetector:
    def __init__(self, model_path: str = "yolov8n.pt", conf: float = 0.40):
        from ultralytics import YOLO

        self.conf = conf
        self.model = YOLO(model_path)
        self.model.to("cpu")
        log.info("YOLOv8n loaded on CPU (model: %s)", model_path)

    def detect(self, frame: np.ndarray) -> list[dict[str, Any]]:
        """Return list of detection dicts from a BGR frame."""
        try:
            results = self.model(frame, conf=self.conf, verbose=False, device="cpu")
            detections: list[dict[str, Any]] = []
            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    label = TARGET_CLASSES.get(cls_id, self.model.names.get(cls_id, "object"))
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    detections.append({
                        "label": label,
                        "confidence": float(box.conf[0]),
                        "bbox": [x1, y1, x2, y2],
                        "bbox_h": max(y2 - y1, 1.0),
                        "bbox_w": max(x2 - x1, 1.0),
                    })
            return detections
        except Exception as exc:
            log.warning("Detection error: %s", exc)
            return []
