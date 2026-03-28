#!/bin/bash
# ============================================================
#  Deploy FastAPI Backend
#  Run from /opt/assistive-vision/
# ============================================================

set -e

APP_DIR="/opt/assistive-vision 1/backend"
echo "[Backend] Setting up Python environment..."

cd "$APP_DIR"

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Pre-download YOLOv8n weights
echo "[Backend] Downloading YOLOv8n weights..."
python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

echo "[Backend] Creating systemd service..."

cat > /etc/systemd/system/assistive-vision-backend.service << 'SERVICE'
[Unit]
Description=AssistiveVision FastAPI Backend
After=network.target ollama.service
Wants=ollama.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/assistive-vision 1/backend
Environment="PATH=/opt/assistive-vision 1/backend/venv/bin"
ExecStart=/opt/assistive-vision 1/backend/venv/bin/python main.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable assistive-vision-backend
systemctl restart assistive-vision-backend

echo ""
echo "[Backend] Service started!"
echo "Check status: systemctl status assistive-vision-backend"
echo "View logs:    journalctl -u assistive-vision-backend -f"
