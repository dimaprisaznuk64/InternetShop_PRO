#!/bin/bash
set -euo pipefail

echo "=== InternetShop PRO — Health Check ==="

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
FAILURES=0

echo "[1/3] Checking backend..."
if STATUS=$(curl -sf "$BACKEND_URL/health" 2>/dev/null); then
    echo "  Backend: OK ($STATUS)"
else
    echo "  Backend: FAIL"
    FAILURES=$((FAILURES + 1))
fi

echo "[2/3] Checking frontend..."
if curl -sf "$FRONTEND_URL" > /dev/null 2>&1; then
    echo "  Frontend: OK"
else
    echo "  Frontend: FAIL"
    FAILURES=$((FAILURES + 1))
fi

echo "[3/3] Checking Docker services..."
if docker compose ps --format json | python3 -c "
import sys, json
services = [json.loads(line) for line in sys.stdin if line.strip()]
unhealthy = [s for s in services if s.get('Health', '') not in ('healthy', '', None)]
if unhealthy:
    print(f'Unhealthy: {[s[\"Name\"] for s in unhealthy]}')
    sys.exit(1)
print('All services healthy')
" 2>/dev/null; then
    echo "  Docker: OK"
else
    echo "  Docker: WARN"
fi

echo ""
if [ $FAILURES -eq 0 ]; then
    echo "=== All checks passed! ==="
else
    echo "=== $FAILURES check(s) failed! ==="
    exit 1
fi
