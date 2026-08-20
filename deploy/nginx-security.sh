#!/bin/bash
set -euo pipefail

echo "=== InternetShop PRO — Nginx Security Hardening ==="

echo "[1/4] Checking nginx installation..."
if ! command -v nginx &> /dev/null; then
    echo "ERROR: nginx not installed"
    exit 1
fi

echo "[2/4] Removing server_tokens..."
if ! grep -q "server_tokens off" /etc/nginx/nginx.conf; then
    sed -i 's/server_tokens on;/server_tokens off;/' /etc/nginx/nginx.conf 2>/dev/null || true
    echo 'server_tokens off;' >> /etc/nginx/nginx.conf
fi

echo "[3/4] Setting security headers..."
if ! grep -q "X-Frame-Options" /etc/nginx/conf.d/security-headers.conf 2>/dev/null; then
    cat > /etc/nginx/conf.d/security-headers.conf << 'EOF'
add_header X-Frame-Options DENY always;
add_header X-Content-Type-Options nosniff always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
EOF
fi

echo "[4/4] Testing nginx config..."
nginx -t

echo ""
echo "=== Nginx hardened! ==="
echo "Headers: X-Frame-Options, X-Content-Type-Options, XSS-Protection"
echo "server_tokens: off"
