#!/bin/bash
set -euo pipefail

echo "=== InternetShop PRO — Server Setup ==="

APP_USER="internetshop"
APP_DIR="/opt/internetshop"

echo "[1/7] System update..."
apt-get update && apt-get upgrade -y

echo "[2/7] Install dependencies..."
apt-get install -y \
    curl \
    wget \
    git \
    ufw \
    fail2ban \
    unattended-upgrades \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

echo "[3/7] Install Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker.gpg] \
        https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
fi
echo "Docker $(docker --version)"

echo "[4/7] Create app user..."
if ! id "$APP_USER" &>/dev/null; then
    adduser --system --group --home "$APP_DIR" "$APP_USER"
fi

echo "[5/7] Create app directory..."
mkdir -p "$APP_DIR"
chown "$APP_USER:$APP_USER" "$APP_DIR"

echo "[6/7] Enable unattended security upgrades..."
dpkg-reconfigure -f noninteractive unattended-upgrades

echo "[7/7] Enable Docker on boot..."
systemctl enable docker
systemctl start docker

echo "=== Server setup complete! ==="
echo "Next: deploy/firewall.sh, deploy/ssh-setup.sh"
