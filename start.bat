@echo off
REM ============================================================
REM  AssistiveVision — Start all services (Windows)
REM  Opens 3 terminal windows: Ollama, Backend, Frontend
REM ============================================================

echo.
echo  Starting AssistiveVision...
echo.

REM ── 1. Start Ollama serve ────────────────────────────────────
echo [1/3] Starting Ollama (Gemma 2B)...
start "Ollama" cmd /k "ollama serve"
timeout /t 3 /nobreak >nul

REM ── 2. Start FastAPI backend ──────────────────────────────────
echo [2/3] Starting FastAPI backend on http://localhost:8000 ...
start "Backend" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate && python main.py"
timeout /t 2 /nobreak >nul

REM ── 3. Start React frontend ──────────────────────────────────
echo [3/3] Starting React frontend on http://localhost:3000 ...
start "Frontend" cmd /k "cd /d %~dp0frontend && npm start"

echo.
echo  All services launched in separate windows.
echo  Open http://localhost:3000 in your browser.
echo.
pause
