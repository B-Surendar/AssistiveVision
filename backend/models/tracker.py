"""
Object Tracker — DeepSORT (deep_sort_realtime)
Assigns stable IDs across frames.
"""

import logging
from typing import Any

import numpy as np

log = logging.getLogger("assistive_vision.tracker")


class ObjectTracker:
    def __init__(self, max_age: int = 30, n_init: int = 2):
        from deep_sort_realtime.deepsort_tracker import DeepSort

        self._tracker = DeepSort(
            max_age=max_age,
            n_init=n_init,
            nms_max_overlap=1.0,
            max_cosine_distance=0.3,
            nn_budget=None,
            embedder="mobilenet",
            half=False,
            bgr=True,
            embedder_gpu=False,   # CPU only
        )
        log.info("DeepSORT initialised (max_age=%d, n_init=%d)", max_age, n_init)

    def update(self, detections: list[dict[str, Any]], frame: np.ndarray) -> list[dict[str, Any]]:
        """Update tracker; return confirmed tracks."""
        if not detections:
            try:
                self._tracker.update_tracks([], frame=frame)
            except Exception:
                pass
            return []

        # DeepSORT expects: ([x1, y1, w, h], confidence, class_label)
        raw = [
            ([d["bbox"][0], d["bbox"][1], d["bbox_w"], d["bbox_h"]], d["confidence"], d["label"])
            for d in detections
        ]
        try:
            tracks = self._tracker.update_tracks(raw, frame=frame)
        except Exception as exc:
            log.warning("Tracker update error: %s", exc)
            return []

        out: list[dict[str, Any]] = []
        for t in tracks:
            if not t.is_confirmed():
                continue
            x1, y1, x2, y2 = t.to_ltrb()
            out.append({
                "track_id": t.track_id,
                "label": t.get_det_class() or "object",
                "confidence": t.get_det_conf() or 0.5,
                "bbox": [x1, y1, x2, y2],
                "bbox_h": max(y2 - y1, 1.0),
            })
        return out
