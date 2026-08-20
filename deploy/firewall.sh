#!/bin/bash
set -euo pipefail

echo "=== InternetShop PRO — Firewall Setup (UFW) ==="

echo "[1/5] Reset UFW to defaults..."
ufw --force reset

echo "[2/5] Set default policies..."
ufw default deny incoming
ufw default allow outgoing

echo "[3/5] Allow SSH..."
ufw allow 22/tcp comment "SSH"

echo "[4/5] Allow HTTP and HTTPS..."
ufw allow 80/tcp comment "HTTP"
ufw allow 443/tcp comment "HTTPS"

echo "[5/5] Enable UFW..."
ufw --force enable
ufw status verbose

echo "=== Firewall configured! ==="
echo "Rules: SSH(22), HTTP(80), HTTPS(443) — all other incoming blocked"
