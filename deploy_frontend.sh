#!/bin/bash
# ============================================================
#  Build and deploy React frontend to Nginx
#  Run from /opt/assistive-vision/
#  Usage: bash deploy_frontend.sh YOUR_DOMAIN_OR_IP
# ============================================================

set -e

DOMAIN=${1:-"YOUR_VPS_IP"}
APP_DIR="/opt/assistive-vision 1/frontend"

echo "[Frontend] Building React app..."
cd "$APP_DIR"

# Set backend WebSocket URL to use your VPS domain/IP
export VITE_WS_URL="wss://${DOMAIN}"

npm install
npm run build

echo "[Frontend] Copying build to Nginx..."
rm -rf /var/www/assistive-vision
cp -r dist /var/www/assistive-vision

echo "[Frontend] Build deployed to /var/www/assistive-vision"
