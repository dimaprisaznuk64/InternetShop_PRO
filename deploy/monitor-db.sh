#!/bin/bash
set -euo pipefail

echo "=== InternetShop PRO — Database Monitor ==="

COMPOSE_FILE="docker-compose.yml"
COMPOSE_PROD="docker-compose.prod.yml"
WARN=0

echo "[1/5] PostgreSQL status..."
PG_STATUS=$(docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD" ps postgres --format json 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())
    print(data.get('State', 'unknown'))
except:
    print('unreachable')
" 2>/dev/null || echo "unreachable")
echo "  Status: $PG_STATUS"

echo "[2/5] PostgreSQL connections..."
PG_CONN=$(docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD" exec -T postgres \
    psql -U postgres -d internetshop -t -c \
    "SELECT count(*) FROM pg_stat_activity WHERE datname='internetshop';" 2>/dev/null | tr -d ' ' || echo "0")
echo "  Active connections: $PG_CONN"
if [ "$PG_CONN" -gt 80 ]; then
    echo "  WARNING: High connection count!"
    WARN=$((WARN + 1))
fi

echo "[3/5] PostgreSQL database size..."
PG_SIZE=$(docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD" exec -T postgres \
    psql -U postgres -d internetshop -t -c \
    "SELECT pg_size_pretty(pg_database_size('internetshop'));" 2>/dev/null | tr -d ' ' || echo "unknown")
echo "  Size: $PG_SIZE"

echo "[4/5] Redis status..."
REDIS_STATUS=$(docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD" exec -T redis \
    redis-cli ping 2>/dev/null || echo "unreachable")
echo "  Status: $REDIS_STATUS"

echo "[5/5] Redis memory..."
REDIS_MEM=$(docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD" exec -T redis \
    redis-cli info memory 2>/dev/null | grep "used_memory_human" | cut -d: -f2 | tr -d '\r' || echo "unknown")
echo "  Used memory: $REDIS_MEM"

echo ""
if [ $WARN -eq 0 ]; then
    echo "=== All checks passed! ==="
else
    echo "=== $WARN warning(s) found ==="
fi
