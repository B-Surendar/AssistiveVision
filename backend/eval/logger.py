"""
Evaluation Logger — appends prediction records to eval/predictions.json
"""

import json
import logging
import os
import threading
from typing import Any

log = logging.getLogger("assistive_vision.eval")

_EVAL_DIR = os.path.dirname(__file__)
PREDICTIONS_PATH = os.path.join(_EVAL_DIR, "predictions.json")


class EvalLogger:
    def __init__(self, flush_every: int = 50):
        os.makedirs(_EVAL_DIR, exist_ok=True)
        self._lock = threading.Lock()
        self._buffer: list[dict] = []
        self._flush_every = flush_every
        log.info("EvalLogger ready → %s", PREDICTIONS_PATH)

    def log(self, frame_id: int, objects: list[dict[str, Any]], delay_ms: float) -> None:
        entry = {
            "frame_id": frame_id,
            "objects": [o["label"] for o in objects],
            "count": len(objects),
            "delay_ms": delay_ms,
        }
        with self._lock:
            self._buffer.append(entry)
            if len(self._buffer) >= self._flush_every:
                self._write()

    def flush(self) -> None:
        with self._lock:
            if self._buffer:
                self._write()

    def _write(self) -> None:
        try:
            existing: list = []
            if os.path.exists(PREDICTIONS_PATH):
                with open(PREDICTIONS_PATH, "r") as f:
                    existing = json.load(f)
            existing.extend(self._buffer)
            with open(PREDICTIONS_PATH, "w") as f:
                json.dump(existing, f, indent=2)
            self._buffer.clear()
        except Exception as exc:
            log.warning("Eval write error: %s", exc)

    def compute_metrics(self) -> dict:
        try:
            if not os.path.exists(PREDICTIONS_PATH):
                return {"error": "No predictions logged yet"}
            with open(PREDICTIONS_PATH, "r") as f:
                data = json.load(f)
            if not data:
                return {"error": "Empty predictions file"}

            n = len(data)
            detected = sum(1 for d in data if d["count"] > 0)
            delays = [d["delay_ms"] for d in data]
            all_labels: list[str] = []
            for d in data:
                all_labels.extend(d["objects"])
            freq: dict[str, int] = {}
            for lbl in all_labels:
                freq[lbl] = freq.get(lbl, 0) + 1

            return {
                "total_frames": n,
                "detected_frames": detected,
                "detection_rate": round(detected / n, 4),
                "avg_objects_per_frame": round(sum(d["count"] for d in data) / n, 2),
                "avg_delay_ms": round(sum(delays) / n, 1),
                "max_delay_ms": round(max(delays), 1),
                "p95_delay_ms": round(sorted(delays)[int(0.95 * n)], 1),
                "label_frequency": freq,
            }
        except Exception as exc:
            log.error("Metrics error: %s", exc)
            return {"error": str(exc)}
