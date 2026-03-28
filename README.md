# AssistiveVision 👁

**Real-time assistive vision system for visually impaired users.**  
YOLOv8n · DeepSORT · EasyOCR · Gemma 2B (Ollama) · FastAPI · React + TypeScript

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Browser (React + TypeScript)                           │
│  VideoFeed ──[WS /ws/frame]──► Backend                  │
│  SceneCaption ◄──[WS /ws/scene]── Backend               │
└─────────────────────────────────────────────────────────┘
                         │
         ┌───────────────▼───────────────┐
         │   FastAPI  (main.py)          │
         │   ┌────────┐  ┌───────────┐  │
         │   │YOLOv8n │  │ DeepSORT  │  │
         │   └────────┘  └───────────┘  │
         │   ┌──────────┐ ┌──────────┐  │
         │   │ EasyOCR  │ │ Distance │  │
         │   └──────────┘ └──────────┘  │
         │   ┌────────────────────────┐ │
         │   │ Ollama HTTP (Gemma 2B) │ │
         │   └────────────────────────┘ │
         └───────────────────────────────┘
```

---

## Requirements

| Tool | Version | Download |
|------|---------|----------|
| Python | 3.10+ | https://python.org |
| Node.js | 18+ | https://nodejs.org |
| Ollama | latest | https://ollama.com/download |
| RAM | 8 GB | — |
| OS | Windows 10/11 | — |

---

## Setup (One Time)

### Step 1 — Clone / extract the project

Place the `assistive-vision/` folder anywhere, e.g. `C:\Projects\assistive-vision\`

### Step 2 — Run the automated setup

```bat
cd C:\Projects\assistive-vision
setup.bat
```

This will:
1. Create a Python virtual environment in `backend/venv/`
2. Install all Python packages (CPU-only PyTorch, ~800 MB)
3. Download YOLOv8n weights (~6 MB)
4. Install Node.js packages for the frontend
5. Download Gemma 2B via Ollama (~1.7 GB, one-time)

> **Total download**: ~2.5 GB on first run. Subsequent starts are instant.

---

## Running

```bat
start.bat
```

This opens **3 terminal windows** automatically:
- **Ollama** — serves Gemma 2B on port 11434
- **Backend** — FastAPI on http://localhost:8000
- **Frontend** — React on http://localhost:3000

Then open **http://localhost:3000** in Chrome/Edge (required for WebRTC webcam).

---

## Manual Start (if start.bat fails)

Open **3 separate Command Prompt** windows:

**Window 1 — Ollama:**
```bat
ollama serve
```

**Window 2 — Backend:**
```bat
cd assistive-vision\backend
venv\Scripts\activate
python main.py
```

**Window 3 — Frontend:**
```bat
cd assistive-vision\frontend
npm start
```

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /health` | REST | System health + pipeline ready status |
| `GET /eval/summary` | REST | Live metrics from eval logger |
| `WS /ws/frame` | WebSocket | Receives base64 JPEG frames from browser |
| `WS /ws/scene` | WebSocket | Pushes scene JSON every 300 ms |

### Scene JSON payload

```json
{
  "objects": [
    {
      "id": "3",
      "label": "person",
      "distance_m": 2.4,
      "direction": "approaching",
      "confidence": 0.87
    }
  ],
  "ocr": ["STOP"],
  "caption": "A person is approaching at 2.4 metres with a STOP sign visible.",
  "confidence": "high",
  "timestamp": 1710000000
}
```

---

## Evaluation

After running the system for a few minutes, generate charts:

```bat
cd backend
venv\Scripts\activate
python eval_metrics.py
```

Outputs written to `backend/eval/`:
- `metrics_report.txt` — text summary
- `precision_recall.png` — PR curve + F1 trend
- `latency_trend.png` — per-frame latency
- `detection_rate.png` — detection rate donut + class frequency

---

## Project Structure

```
assistive-vision/
├── setup.bat                  ← one-time install
├── start.bat                  ← launch all services
│
├── backend/
│   ├── main.py                ← FastAPI app
│   ├── requirements.txt
│   ├── eval_metrics.py        ← run to generate charts
│   ├── models/
│   │   ├── detector.py        ← YOLOv8n
│   │   ├── tracker.py         ← DeepSORT
│   │   ├── distance.py        ← monocular depth
│   │   ├── ocr_engine.py      ← EasyOCR
│   │   └── captioner.py       ← Gemma 2B via Ollama
│   └── eval/
│       ├── logger.py          ← prediction logger
│       └── predictions.json   ← auto-generated
│
└── frontend/
    ├── package.json
    ├── tsconfig.json
    └── src/
        ├── App.tsx
        ├── App.css
        ├── index.tsx
        ├── types/index.ts
        ├── context/SceneContext.tsx
        ├── hooks/
        │   ├── useFrameSender.ts
        │   └── useVoiceFeedback.ts
        └── components/
            ├── VideoFeed.tsx
            ├── SceneCaption.tsx
            ├── ObjectList.tsx
            └── AssistantStatus.tsx
```

---

## Performance Tips (8 GB RAM)

| Tip | Effect |
|-----|--------|
| Use Chrome/Edge (not Firefox) | Better WebRTC performance |
| Close other browser tabs | Frees ~200–500 MB RAM |
| Frame sent every 200 ms (5 FPS) | Configurable in `useFrameSender.ts` |
| OCR runs every 4th frame | Configurable in `main.py` (`frame_id % 4`) |
| Gemma called every 2nd frame | Configurable in `captioner.py` (`% 2`) |
| YOLOv8n is ~6 MB, runs in ~80 ms CPU | Upgrade to yolov8s for better accuracy |

---

## Troubleshooting

### "Ollama not reachable" in backend logs
- Ensure `ollama serve` is running before starting the backend
- Check port 11434 is not blocked by firewall

### Camera not starting
- Allow camera access in browser when prompted
- Try `http://localhost:3000` (not `127.0.0.1`) — some browsers differ

### "No module named ultralytics"
- Make sure you activated the venv: `venv\Scripts\activate`

### High latency (>500 ms)
- Lower `FRAME_INTERVAL_MS` in `useFrameSender.ts` to 300+
- Increase `frame_id % N` OCR skip in `main.py`

### YOLOv8n not detecting well
- Improve lighting
- Move camera closer (< 5 m)
- Lower `conf` threshold in `detector.py` (default: 0.40)

---

## Voice Feedback

Click **🔇 Voice OFF** in the top bar to enable text-to-speech.  
Uses the browser's built-in Web Speech API — no extra install needed.  
Each caption is spoken once with a 2-second cooldown between phrases.

---

## License

MIT — free to use, modify, and distribute.
