"""
Monocular Distance Estimator
distance_m = (real_height_m × focal_length_px) / bbox_height_px
"""

import logging

log = logging.getLogger("assistive_vision.distance")

# Average real-world heights (metres)
REAL_HEIGHTS: dict[str, float] = {
    "person": 1.70,
    "car": 1.50,
    "truck": 2.50,
    "bus": 3.00,
    "motorcycle": 1.10,
    "bicycle": 1.00,
    "dog": 0.50,
    "cat": 0.30,
    "backpack": 0.50,
    "suitcase": 0.70,
    "handbag": 0.35,
    "umbrella": 0.90,
    "chair": 0.90,
    "dining table": 0.75,
    "bottle": 0.25,
    "cell phone": 0.14,
    "laptop": 0.30,
    "book": 0.22,
    "tv": 0.60,
    "traffic light": 2.50,
    "stop sign": 0.75,
    "default": 0.80,
}

# Focal length for ~640 px wide, 60° horizontal FOV camera
FOCAL_LENGTH_PX = 600.0


class DistanceEstimator:
    def __init__(self, focal_length: float = FOCAL_LENGTH_PX):
        self._focal = focal_length
        self._prev: dict[int, float] = {}   # track_id → last distance
        log.info("DistanceEstimator ready (f=%.0f px)", focal_length)

    def estimate(self, label: str, bbox_h_px: float) -> float:
        real_h = REAL_HEIGHTS.get(label, REAL_HEIGHTS["default"])
        d = (real_h * self._focal) / max(bbox_h_px, 1.0)
        return round(max(0.3, min(d, 30.0)), 2)

    def get_motion(self, track_id: int, current_dist: float) -> str:
        THRESHOLD = 0.25   # metres per frame pair
        prev = self._prev.get(track_id)
        self._prev[track_id] = current_dist
        if prev is None:
            return "stationary"
        delta = current_dist - prev
        if delta < -THRESHOLD:
            return "approaching"
        if delta > THRESHOLD:
            return "moving away"
        return "stationary"

    def cleanup(self, active_ids: set[int]) -> None:
        stale = [k for k in self._prev if k not in active_ids]
        for k in stale:
            del self._prev[k]
