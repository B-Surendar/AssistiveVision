#!/bin/bash
# ============================================================
#  AssistiveVision — VPS Server Setup Script
#  Run as root on Ubuntu 22.04
#  Usage: bash server_setup.sh
# ============================================================

set -e  # exit on any error

echo ""
echo "=============================================="
echo "  AssistiveVision VPS Setup"
echo "=============================================="
echo ""

# ── System update ─────────────────────────────────────────────
echo "[1/8] Updating system packages..."
apt-get update -y && apt-get upgrade -y

# ── Install dependencies ──────────────────────────────────────
echo "[2/8] Installing system dependencies..."
apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    git \
    curl \
    wget \
    nginx \
    certbot \
    python3-certbot-nginx \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1

# ── Install Node.js 20 ────────────────────────────────────────
echo "[3/8] Installing Node.js 20..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# ── Install Ollama ────────────────────────────────────────────
echo "[4/8] Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
systemctl enable ollama
systemctl start ollama
sleep 3

# Pull Gemma 2B
echo "  Pulling Gemma 2B model (~1.7 GB)..."
ollama pull gemma:2b

# ── Create app user ───────────────────────────────────────────
echo "[5/8] Creating app user..."
id -u appuser &>/dev/null || useradd -m -s /bin/bash appuser

# ── Clone project ─────────────────────────────────────────────
echo "[6/8] Setting up project directory..."
mkdir -p /opt/assistive-vision
chown appuser:appuser /opt/assistive-vision

echo ""
echo "=============================================="
echo "  Base setup complete!"
echo "  Next: Upload your project files to"
echo "  /opt/assistive-vision/"
echo "  Then run: bash deploy_backend.sh"
echo "  And:      bash deploy_frontend.sh"
echo "=============================================="
