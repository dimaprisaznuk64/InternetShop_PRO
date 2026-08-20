#!/bin/bash
set -euo pipefail

echo "============================================="
echo "  InternetShop PRO — Database Audit"
echo "============================================="

COMPOSE_FILE="docker-compose.yml"
COMPOSE_PROD="docker-compose.prod.yml"

echo ""
echo "=== [1/7] PostgreSQL status ==="
PG_STATUS=$(docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD" ps postgres --format json 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())
    print(data.get('State', 'unknown'))
except:
    print('unreachable')
" 2>/dev/null || echo "unreachable")
echo "  Status: $PG_STATUS"

echo ""
echo "=== [2/7] Active connections ==="
PG_CONN=$(docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD" exec -T postgres \
    psql -U postgres -d internetshop -t -c \
    "SELECT count(*) FROM pg_stat_activity WHERE datname='internetshop';" 2>/dev/null | tr -d ' ' || echo "0")
echo "  Connections: $PG_CONN"
if [ "$PG_CONN" -gt 80 ]; then
    echo "  ⚠ WARNING: High connection count"
fi

echo ""
echo "=== [3/7] Database size ==="
PG_SIZE=$(docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD" exec -T postgres \
    psql -U postgres -d internetshop -t -c \
    "SELECT pg_size_pretty(pg_database_size('internetshop'));" 2>/dev/null | tr -d ' ' || echo "unknown")
echo "  Size: $PG_SIZE"

echo ""
echo "=== [4/7] Table sizes ==="
docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD" exec -T postgres \
    psql -U postgres -d internetshop -c \
    "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
     FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC LIMIT 10;" 2>/dev/null || echo "  Could not query"

echo ""
echo "=== [5/7] Table bloat (dead tuples) ==="
docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD" exec -T postgres \
    psql -U postgres -d internetshop -c \
    "SELECT relname, n_dead_tup, n_live_tup,
            CASE WHEN n_live_tup > 0
                 THEN round(100.0 * n_dead_tup / n_live_tup, 1)
                 ELSE 0 END AS dead_pct
     FROM pg_stat_user_tables WHERE n_dead_tup > 1000
     ORDER BY n_dead_tup DESC LIMIT 5;" 2>/dev/null || echo "  Could not query"

echo ""
echo "=== [6/7] Missing indexes ==="
docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD" exec -T postgres \
    psql -U postgres -d internetshop -c \
    "SELECT relname, seq_scan, idx_scan,
            CASE WHEN seq_scan + idx_scan > 0
                 THEN round(100.0 * idx_scan / (seq_scan + idx_scan), 1)
                 ELSE 0 END AS idx_usage_pct
     FROM pg_stat_user_tables
     WHERE seq_scan > 100 AND (idx_scan IS NULL OR idx_scan = 0)
     ORDER BY seq_scan DESC LIMIT 5;" 2>/dev/null || echo "  Could not query"

echo ""
echo "=== [7/7] Redis status ==="
REDIS_STATUS=$(docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD" exec -T redis \
    redis-cli ping 2>/dev/null || echo "unreachable")
echo "  Status: $REDIS_STATUS"

REDIS_MEM=$(docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD" exec -T redis \
    redis-cli info memory 2>/dev/null | grep "used_memory_human" | cut -d: -f2 | tr -d '\r' || echo "unknown")
echo "  Memory: $REDIS_MEM"

REDIS_KEYS=$(docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD" exec -T redis \
    redis-cli dbsize 2>/dev/null | awk '{print $2}' || echo "unknown")
echo "  Keys: $REDIS_KEYS"

echo ""
echo "============================================="
echo "  Database audit complete"
echo "============================================="
