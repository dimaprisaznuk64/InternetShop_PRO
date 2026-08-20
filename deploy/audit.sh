#!/bin/bash
set -euo pipefail

echo "============================================="
echo "  InternetShop PRO — Full Production Audit"
echo "============================================="
echo "  Date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "  Host: $(hostname)"
echo ""

ERRORS=0

run_check() {
    local name="$1"
    local script="$2"
    echo "--- $name ---"
    if [ -f "$script" ]; then
        bash "$script" || ERRORS=$((ERRORS+1))
    else
        echo "  Script not found: $script"
        ERRORS=$((ERRORS+1))
    fi
    echo ""
}

run_check "Security Audit" "deploy/audit-security.sh"
run_check "Database Audit" "deploy/audit-db.sh"

echo "--- Docker Status ---"
docker compose ps 2>/dev/null || echo "  Docker Compose not available"
echo ""

echo "--- Disk Usage ---"
df -h / 2>/dev/null | head -2
echo ""

echo "--- Memory Usage ---"
free -h 2>/dev/null || echo "  free not available"
echo ""

echo "--- Uptime ---"
uptime 2>/dev/null || echo "  uptime not available"
echo ""

echo "============================================="
if [ $ERRORS -eq 0 ]; then
    echo "  ✅ Full audit completed successfully!"
else
    echo "  ⚠ Audit completed with $ERRORS script error(s)"
fi
echo "============================================="
