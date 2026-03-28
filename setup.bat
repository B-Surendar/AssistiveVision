@echo off
REM ============================================================
REM  AssistiveVision — Windows Setup Script
REM  Run once to install all dependencies.
REM  Requires: Python 3.10+, Node.js 18+, Ollama
REM ============================================================

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║     AssistiveVision — Setup (Windows)        ║
echo  ╚══════════════════════════════════════════════╝
echo.

REM ── Check Python ─────────────────────────────────────────────
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python not found. Install Python 3.10+ from https://python.org
    pause & exit /b 1
)

REM ── Check Node ───────────────────────────────────────────────
node --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Node.js not found. Install from https://nodejs.org
    pause & exit /b 1
)

REM ── Check Ollama ─────────────────────────────────────────────
ollama --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Ollama not found. Download from https://ollama.com/download
    pause & exit /b 1
)

echo [OK] Python, Node.js, and Ollama found.
echo.

REM ── Backend venv ─────────────────────────────────────────────
echo [1/5] Creating Python virtual environment...
cd backend
python -m venv venv
call venv\Scripts\activate.bat

echo [2/5] Installing Python dependencies (CPU torch — ~800 MB)...
pip install --upgrade pip
pip install -r requirements.txt

echo [3/5] Pre-downloading YOLOv8n weights...
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

cd ..

REM ── Frontend ─────────────────────────────────────────────────
echo [4/5] Installing frontend dependencies...
cd frontend
npm install
cd ..

REM ── Ollama model ─────────────────────────────────────────────
echo [5/5] Pulling Gemma 2B model via Ollama (~1.7 GB, one-time download)...
ollama pull gemma:2b

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║  Setup complete!  Run start.bat to launch.   ║
echo  ╚══════════════════════════════════════════════╝
pause
