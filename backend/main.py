"""
Assistive Vision System — FastAPI Backend
Gemma 2B via Ollama + YOLOv8n + DeepSORT + EasyOCR
CPU-optimised for 8 GB RAM / Windows
ngrok-compatible CORS configuration
"""

import asyncio
import base64
import json
import logging
import threading
import time
from contextlib import asynccontextmanager
from typing import Optional

import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from models.detector import ObjectDetector
from models.tracker import ObjectTracker
from models.ocr_engine import OCREngine
from models.captioner import SceneCaptioner
from models.distance import DistanceEstimator
from eval.logger import EvalLogger

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("assistive_vision")


class SharedState:
    def __init__(self):
        self._lock = threading.Lock()
        self._data: dict = {
            "objects": [],
            "ocr": [],
            "caption": "Initialising system…",
            "confidence": "low",
            "timestamp": int(time.time()),
        }
        self.latest_frame: Optional[np.ndarray] = None
        self.frame_id: int = 0

    def update(self, data: dict) -> None:
        with self._lock:
            self._data.update(data)

    def get(self) -> dict:
        with self._lock:
            return dict(self._data)

    def set_frame(self, frame: np.ndarray) -> None:
        with self._lock:
            self.latest_frame = frame
            self.frame_id += 1

    def get_frame(self):
        with self._lock:
            return self.latest_frame, self.frame_id


state = SharedState()

detector: Optional[ObjectDetector] = None
tracker: Optional[ObjectTracker] = None
ocr_engine: Optional[OCREngine] = None
captioner: Optional[SceneCaptioner] = None
distance_estimator: Optional[DistanceEstimator] = None
eval_logger: Optional[EvalLogger] = None
pipeline_ready = False


def init_pipeline() -> None:
    global detector, tracker, ocr_engine, captioner
    global distance_estimator, eval_logger, pipeline_ready

    try:
        log.info("Loading YOLOv8n detector…")
        detector = ObjectDetector()

        log.info("Loading DeepSORT tracker…")
        tracker = ObjectTracker()

        log.info("Loading EasyOCR…")
        ocr_engine = OCREngine()

        log.info("Connecting to Ollama (Gemma 2B)…")
        captioner = SceneCaptioner()

        log.info("Loading distance estimator…")
        distance_estimator = DistanceEstimator()

        log.info("Starting eval logger…")
        eval_logger = EvalLogger()

        pipeline_ready = True
        log.info("✅  Pipeline ready.")
        state.update({"caption": "System ready — point your camera at the scene."})

    except Exception as exc:
        log.error("Pipeline init failed: %s", exc, exc_info=True)
        state.update({"caption": f"Startup error: {exc}"})


_last_processed_id = -1


def process_frame_worker() -> None:
    global _last_processed_id
    while True:
        try:
            if not pipeline_ready:
                time.sleep(0.1)
                continue

            frame, frame_id = state.get_frame()
            if frame is None or frame_id == _last_processed_id:
                time.sleep(0.05)
                continue

            _last_processed_id = frame_id
            t0 = time.time()

            detections = detector.detect(frame)
            tracked = tracker.update(detections, frame)

            objects_out = []
            for obj in tracked:
                dist = distance_estimator.estimate(obj["label"], obj["bbox_h"])
                direction = distance_estimator.get_motion(obj["track_id"], dist)
                objects_out.append({
                    "id": str(obj["track_id"]),
                    "label": obj["label"],
                    "distance_m": round(dist, 2),
                    "direction": direction,
                    "confidence": round(obj["confidence"], 2),
                })

            ocr_texts: list[str] = []
            if frame_id % 4 == 0:
                ocr_texts = ocr_engine.extract(frame)

            caption = captioner.generate(objects_out, ocr_texts)
            confidence = "high" if objects_out else "low"

            state.update({
                "objects": objects_out,
                "ocr": ocr_texts,
                "caption": caption,
                "confidence": confidence,
                "timestamp": int(time.time()),
            })

            delay_ms = round((time.time() - t0) * 1000, 1)
            eval_logger.log(frame_id, objects_out, delay_ms)

        except Exception as exc:
            log.warning("Worker error: %s", exc)
            time.sleep(0.1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    threading.Thread(target=init_pipeline, daemon=True).start()
    threading.Thread(target=process_frame_worker, daemon=True).start()
    yield
    if eval_logger:
        eval_logger.flush()
    log.info("Server shut down.")


app = FastAPI(
    title="Assistive Vision API",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS — allow ALL origins so ngrok + Vercel both work ─────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "pipeline_ready": pipeline_ready}


@app.get("/eval/summary")
async def eval_summary():
    if eval_logger:
        return eval_logger.compute_metrics()
    return {"error": "Eval logger not ready"}


@app.websocket("/ws/frame")
async def ws_frame(websocket: WebSocket):
    # Accept from any origin (required for ngrok tunnelling)
    await websocket.accept()
    log.info("Frame WS connected from %s", websocket.client)
    try:
        while True:
            data: str = await websocket.receive_text()
            try:
                if "," in data:
                    data = data.split(",", 1)[1]
                raw = base64.b64decode(data)
                arr = np.frombuffer(raw, dtype=np.uint8)
                frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                if frame is not None:
                    frame = cv2.resize(frame, (640, 480))
                    state.set_frame(frame)
            except Exception as exc:
                log.debug("Frame decode error: %s", exc)
    except WebSocketDisconnect:
        log.info("Frame WS disconnected")


@app.websocket("/ws/scene")
async def ws_scene(websocket: WebSocket):
    await websocket.accept()
    log.info("Scene WS connected from %s", websocket.client)
    try:
        while True:
            await asyncio.sleep(0.3)
            await websocket.send_text(json.dumps(state.get()))
    except WebSocketDisconnect:
        log.info("Scene WS disconnected")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False, workers=1)