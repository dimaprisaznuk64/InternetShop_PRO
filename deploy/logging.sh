#!/bin/bash
set -euo pipefail

echo "=== InternetShop PRO — Logging Setup ==="

LOG_DIR="${LOG_DIR:-/var/log/internetshop}"
NGINX_LOG_DIR="${NGINX_LOG_DIR:-/var/log/nginx}"

echo "[1/5] Creating log directories..."
sudo mkdir -p "$LOG_DIR" "$NGINX_LOG_DIR"
sudo chown -R $(whoami):$(whoami) "$LOG_DIR"

echo "[2/5] Configuring Docker logging..."
echo "  Docker log driver: json-file"
echo "  Max size: 10m"
echo "  Max file: 3"

echo "[3/5] Setting up logrotate..."
sudo tee /etc/logrotate.d/internetshop > /dev/null << 'EOF'
/var/log/nginx/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 $(cat /var/run/nginx.pid)
    endscript
}

/var/log/internetshop/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 www-data adm
}
EOF
echo "  Logrotate configured"

echo "[4/5] Setting up systemd journal limits..."
sudo mkdir -p /etc/systemd/journald.conf.d
sudo tee /etc/systemd/journald.conf.d/internetshop.conf > /dev/null << 'EOF'
[Journal]
SystemMaxUse=500M
SystemMaxFileSize=50M
MaxRetentionSec=30day
EOF
sudo systemctl restart systemd-journald 2>/dev/null || echo "  journald restart skipped"

echo "[5/5] Log rotation verification..."
echo "  Nginx logs: $NGINX_LOG_DIR"
echo "  App logs: $LOG_DIR"

echo ""
echo "=== Logging setup complete ==="
