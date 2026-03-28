"""
Scene Captioner — Gemma 2B via Ollama
Generates rich 3-line scene descriptions for visually impaired users.
Runs in background thread — never blocks the main pipeline.
"""

import logging
import threading
import time
import urllib.request
import urllib.error
import json
from typing import Any

log = logging.getLogger("assistive_vision.captioner")

OLLAMA_URL   = "http://localhost:11434/api/generate"
OLLAMA_CHECK = "http://localhost:11434/"
MODEL_NAME   = "gemma:2b"
TIMEOUT      = 25
RETRY_EVERY  = 15


class SceneCaptioner:
    def __init__(self):
        self._lock            = threading.Lock()
        self._ollama_ok       = False
        self._last_retry_time = 0.0
        self._last_caption    = ""
        self._pending         = False
        self._frame_counter   = 0
        self._pending_objects: list[dict] = []
        self._pending_ocr:     list[str]  = []

        threading.Thread(target=self._try_reconnect, daemon=True).start()

    # ── Public ────────────────────────────────────────────────────────────────

    def generate(self, objects: list[dict[str, Any]], ocr_texts: list[str]) -> str:
        self._frame_counter += 1

        if not objects:
            return "No objects detected in the scene. The area ahead appears to be clear."

        if not self._ollama_ok:
            if time.time() - self._last_retry_time >= RETRY_EVERY:
                threading.Thread(target=self._try_reconnect, daemon=True).start()

        if self._ollama_ok and self._frame_counter % 6 == 0 and not self._pending:
            with self._lock:
                self._pending_objects = list(objects)
                self._pending_ocr     = list(ocr_texts)
                self._pending         = True
            threading.Thread(target=self._background_call, daemon=True).start()

        with self._lock:
            if self._last_caption:
                return self._last_caption

        return self._template(objects, ocr_texts)

    # ── Background thread ─────────────────────────────────────────────────────

    def _background_call(self) -> None:
        with self._lock:
            objects   = list(self._pending_objects)
            ocr_texts = list(self._pending_ocr)

        caption = self._call_ollama(objects, ocr_texts)

        with self._lock:
            if caption:
                self._last_caption = caption
                log.info("Gemma caption: %s", caption)
            self._pending = False

    # ── Ollama helpers ────────────────────────────────────────────────────────

    def _try_reconnect(self) -> None:
        self._last_retry_time = time.time()
        ok = self._ping_ollama()
        if ok and not self._ollama_ok:
            log.info("Ollama connected — Gemma 2B captions active.")
        elif not ok:
            log.warning("Ollama not reachable — retrying in %ds.", RETRY_EVERY)
        self._ollama_ok = ok

    def _ping_ollama(self) -> bool:
        try:
            with urllib.request.urlopen(OLLAMA_CHECK, timeout=3):
                return True
        except Exception:
            return False

    def _build_prompt(self, objects: list[dict], ocr_texts: list[str]) -> str:
        primary = objects[0]
        p_label = primary["label"]
        p_dist  = primary["distance_m"]
        p_dir   = primary["direction"]

        # Danger level based on distance + direction
        if p_dist < 1.5 and p_dir == "approaching":
            danger = "DANGER — immediate obstacle very close and approaching fast"
        elif p_dist < 2.5 and p_dir == "approaching":
            danger = "CAUTION — object is nearby and approaching"
        elif p_dist < 1.5:
            danger = "CAUTION — object is very close"
        else:
            danger = "SAFE — object is at a comfortable distance"

        # Build full scene data string
        scene_lines = []
        for i, obj in enumerate(objects[:4]):
            scene_lines.append(
                f"  Object {i+1}: {obj['label']} — {obj['direction']} at {obj['distance_m']} metres"
            )
        scene_str = "\n".join(scene_lines)

        ocr_str = f"\n  Visible text/signs: {', '.join(ocr_texts[:3])}" if ocr_texts else ""
        danger_str = f"\n  Safety assessment: {danger}"

        prompt = f"""You are a helpful AI assistant guiding a visually impaired person in real time.

Scene data detected by sensors:
{scene_str}{ocr_str}{danger_str}

Write a description in EXACTLY 3 sentences. Follow this structure:
- Sentence 1: Describe the closest or most important object. Include its exact distance in metres and use the word "{p_dir}" to describe its movement.
- Sentence 2: Describe the overall environment — mention any other objects, their distances, and whether the path looks clear or busy.
- Sentence 3: Give a practical safety tip or action the person should take right now based on what is detected.

Rules:
- Always include the actual distance numbers from the data
- Use "approaching", "moving away", or "stationary" exactly — never paraphrase them
- Be clear, direct and helpful — this person cannot see
- Do NOT use phrases like "clearly defined", "fixed location", "measuring device"
- Output only the 3 sentences, nothing else

Description:"""

        return prompt

    def _call_ollama(self, objects: list[dict], ocr_texts: list[str]) -> str:
        prompt  = self._build_prompt(objects, ocr_texts)
        payload = json.dumps({
            "model":  MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": 150,   # enough for 3 sentences
                "temperature": 0.2,
                "top_p":       0.9,
                "top_k":       30,
                "num_ctx":     1024,
            },
        }).encode()

        req = urllib.request.Request(
            OLLAMA_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                data = json.loads(resp.read().decode())
                raw  = data.get("response", "").strip()

                # Strip any echoed prefix
                for prefix in ["Description:", "Sentence:", "Response:", "Answer:"]:
                    if raw.lower().startswith(prefix.lower()):
                        raw = raw[len(prefix):].strip()

                # Extract up to 3 clean sentences
                sentences = []
                for part in raw.replace("!", ".").replace("?", ".").split("."):
                    part = part.strip()
                    if len(part) > 10:
                        sentences.append(part + ".")
                    if len(sentences) == 3:
                        break

                caption = " ".join(sentences).strip()

                # Validate: must contain actual distance + direction word
                p_dir  = objects[0]["direction"]
                p_dist = str(objects[0]["distance_m"])

                if p_dist not in caption or p_dir not in caption.lower():
                    log.debug("Gemma missed distance/direction — using template. Raw: %s", raw)
                    return self._template(objects, ocr_texts)

                return caption if len(caption) > 20 else ""

        except urllib.error.URLError as exc:
            log.warning("Ollama request failed: %s", exc)
            self._ollama_ok       = False
            self._last_retry_time = time.time()
            return ""

        except Exception as exc:
            log.debug("Ollama call error: %s", exc)
            return ""

    @staticmethod
    def _template(objects: list[dict], ocr_texts: list[str]) -> str:
        """
        Rich 3-sentence template used when Ollama is unavailable
        or Gemma ignores instructions.
        """
        primary   = objects[0]
        label     = primary["label"]
        dist      = primary["distance_m"]
        direction = primary["direction"]

        # Sentence 1 — primary object with direction
        if direction == "approaching":
            s1 = f"A {label} is approaching you at {dist} metres — it is getting closer."
        elif direction == "moving away":
            s1 = f"A {label} is moving away from you at {dist} metres."
        else:
            s1 = f"A {label} is stationary at {dist} metres directly ahead of you."

        # Sentence 2 — environment summary
        if len(objects) == 1:
            if dist < 2.0:
                s2 = "The immediate area is occupied — the path ahead is blocked."
            else:
                s2 = "No other objects are detected nearby — the surrounding area appears clear."
        else:
            other_parts = []
            for obj in objects[1:3]:
                lbl = obj["label"]
                d   = obj["distance_m"]
                dr  = obj["direction"]
                if dr == "approaching":
                    other_parts.append(f"a {lbl} approaching at {d} metres")
                elif dr == "moving away":
                    other_parts.append(f"a {lbl} moving away at {d} metres")
                else:
                    other_parts.append(f"a {lbl} stationary at {d} metres")
            s2 = f"Additionally, {'; '.join(other_parts)} {'is' if len(other_parts)==1 else 'are'} detected in the scene."

        # Add OCR to sentence 2 if present
        if ocr_texts:
            s2 += f" A sign reads: {', '.join(ocr_texts[:2])}."

        # Sentence 3 — safety advice
        if direction == "approaching" and dist < 1.5:
            s3 = "Stop immediately — an object is very close and moving towards you."
        elif direction == "approaching" and dist < 3.0:
            s3 = "Slow down and be cautious — an object is approaching from ahead."
        elif direction == "approaching":
            s3 = "Stay alert and be ready to stop — an object is moving in your direction."
        elif dist < 1.5:
            s3 = "Move carefully — there is an object very close to you."
        elif len(objects) > 2:
            s3 = "Proceed slowly — multiple objects are present in the environment."
        else:
            s3 = "You may proceed with normal caution — the path appears manageable."

        return f"{s1} {s2} {s3}"