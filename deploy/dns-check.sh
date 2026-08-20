#!/bin/bash
set -euo pipefail

echo "=== InternetShop PRO — DNS Check ==="

DOMAIN="${1:?Usage: $0 <domain.com>}"
SERVER_IP="${2:?Usage: $0 <domain.com> <server-ip>}"
FAILURES=0

echo "Domain: $DOMAIN"
echo "Expected IP: $SERVER_IP"
echo ""

echo "[1/3] Checking A record..."
ACTUAL_IP=$(dig +short "$DOMAIN" A | tail -1)
if [ "$ACTUAL_IP" = "$SERVER_IP" ]; then
    echo "  A record: OK ($ACTUAL_IP)"
else
    echo "  A record: FAIL (got '$ACTUAL_IP', expected '$SERVER_IP')"
    FAILURES=$((FAILURES + 1))
fi

echo "[2/3] Checking www CNAME..."
WWW_IP=$(dig +short "www.$DOMAIN" A | tail -1)
if [ "$WWW_IP" = "$SERVER_IP" ] || [ "$WWW_IP" = "$DOMAIN" ]; then
    echo "  www: OK ($WWW_IP)"
else
    echo "  www: WARN (got '$WWW_IP')"
fi

echo "[3/3] Checking DNS propagation..."
for ns in 8.8.8.8 1.1.1.1 208.67.222.222; do
    NS_IP=$(dig +short "@$ns" "$DOMAIN" A | tail -1)
    if [ "$NS_IP" = "$SERVER_IP" ]; then
        echo "  $ns: OK"
    else
        echo "  $ns: NOT YET ($NS_IP)"
        FAILURES=$((FAILURES + 1))
    fi
done

echo ""
if [ $FAILURES -eq 0 ]; then
    echo "=== DNS fully propagated! ==="
else
    echo "=== $FAILURES check(s) need attention ==="
fi
