#!/bin/bash
set -euo pipefail

echo "============================================="
echo "  InternetShop PRO — Performance Check"
echo "============================================="

COMPOSE_FILE="docker-compose.yml"
COMPOSE_PROD="docker-compose.prod.yml"

echo ""
echo "=== [1/6] API response time ==="
API_URL="${API_URL:-http://localhost:8000}"
for endpoint in "/" "/docs" "/health"; do
    STATUS=$(curl -o /dev/null -s -w "%{http_code}" --max-time 5 "${API_URL}${endpoint}" 2>/dev/null || echo "000")
    TIME=$(curl -o /dev/null -s -w "%{time_total}" --max-time 5 "${API_URL}${endpoint}" 2>/dev/null || echo "timeout")
    echo "  ${endpoint}: ${STATUS} (${TIME}s)"
done

echo ""
echo "=== [2/6] PostgreSQL cache hit ratio ==="
CACHE_HIT=$(docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD" exec -T postgres \
    psql -U postgres -d internetshop -t -c \
    "SELECT round(100.0 * sum(blks_hit) / (sum(blks_hit) + sum(blks_read) + 1), 2) FROM pg_stat_database WHERE datname = current_database();" 2>/dev/null | tr -d ' ' || echo "unknown")
echo "  Cache hit ratio: ${CACHE_HIT}%"
if [ "$CACHE_HIT" != "unknown" ]; then
    HIT_INT=$(echo "$CACHE_HIT" | cut -d. -f1)
    if [ "$HIT_INT" -lt 95 ]; then
        echo "  ⚠ WARNING: Cache hit ratio below 95%"
    fi
fi

echo ""
echo "=== [3/6] Slow queries (>1s) ==="
docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD" exec -T postgres \
    psql -U postgres -d internetshop -c \
    "SELECT count(*) AS slow_count FROM pg_stat_activity
     WHERE state = 'active'
     AND now() - query_start > interval '1 second'
     AND query NOT LIKE '%pg_stat_activity%';" 2>/dev/null || echo "  Could not query"

echo ""
echo "=== [4/6] Table bloat ==="
docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD" exec -T postgres \
    psql -U postgres -d internetshop -t -c \
    "SELECT relname, n_dead_tup, n_live_tup
     FROM pg_stat_user_tables
     WHERE n_dead_tup > 1000
     ORDER BY n_dead_tup DESC LIMIT 5;" 2>/dev/null || echo "  Could not query"

echo ""
echo "=== [5/6] Redis hit rate ==="
REDIS_STATS=$(docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD" exec -T redis \
    redis-cli info stats 2>/dev/null || echo "")
if [ -n "$REDIS_STATS" ]; then
    HITS=$(echo "$REDIS_STATS" | grep "keyspace_hits:" | cut -d: -f2 | tr -d '\r' || echo "0")
    MISSES=$(echo "$REDIS_STATS" | grep "keyspace_misses:" | cut -d: -f2 | tr -d '\r' || echo "0")
    TOTAL=$((HITS + MISSES))
    if [ "$TOTAL" -gt 0 ]; then
        HIT_RATE=$((HITS * 100 / TOTAL))
        echo "  Hit rate: ${HIT_RATE}% (${HITS} hits, ${MISSES} misses)"
    else
        echo "  No data yet"
    fi
else
    echo "  Redis unreachable"
fi

echo ""
echo "=== [6/6] Docker resource usage ==="
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null || echo "  Docker stats unavailable"

echo ""
echo "============================================="
echo "  Performance check complete"
echo "============================================="
