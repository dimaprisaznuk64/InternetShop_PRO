#!/bin/bash
set -euo pipefail

echo "=== InternetShop PRO — SSL Setup (Let's Encrypt) ==="

DOMAIN="${1:?Usage: $0 <domain.com>}"
EMAIL="${2:?Usage: $0 <domain.com> <email@example.com>}"
WEBROOT="/var/www/internetshop"

echo "[1/5] Installing certbot..."
apt-get install -y certbot python3-certbot-nginx

echo "[2/5] Obtaining SSL certificate for $DOMAIN..."
certbot certonly \
    --webroot \
    --webroot-path "$WEBROOT" \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN" \
    -d "www.$DOMAIN"

echo "[3/5] Configuring nginx for SSL..."
cat > /etc/nginx/sites-available/internetshop.conf << NGINX
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;

    root $WEBROOT;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/internetshop.conf /etc/nginx/sites-enabled/internetshop.conf
rm -f /etc/nginx/sites-enabled/default

echo "[4/5] Testing nginx config..."
nginx -t

echo "[5/5] Reloading nginx..."
systemctl reload nginx

echo ""
echo "=== SSL setup complete! ==="
echo "Certificate: /etc/letsencrypt/live/$DOMAIN/"
echo "Auto-renewal: certbot renews automatically via systemd timer"
echo ""
echo "Verify: https://$DOMAIN"
