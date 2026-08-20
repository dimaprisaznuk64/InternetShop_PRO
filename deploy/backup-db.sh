#!/bin/bash
set -euo pipefail

echo "=== InternetShop PRO — Database Backup ==="

BACKUP_DIR="/opt/internetshop/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/internetshop_${DATE}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "[1/3] Creating backup..."
docker compose exec -T postgres pg_dump \
    -U "${POSTGRES_USER:-postgres}" \
    -d "${POSTGRES_DB:-internetshop}" \
    --no-owner --no-acl | gzip > "$BACKUP_FILE"

echo "[2/3] Verifying backup..."
if [ -s "$BACKUP_FILE" ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "Backup created: $BACKUP_FILE ($SIZE)"
else
    echo "ERROR: Backup file is empty!"
    rm -f "$BACKUP_FILE"
    exit 1
fi

echo "[3/3] Cleaning old backups (keeping last 7)..."
cd "$BACKUP_DIR"
ls -t internetshop_*.sql.gz 2>/dev/null | tail -n +8 | xargs -r rm --

echo "=== Backup complete! ==="
echo "Location: $BACKUP_FILE"
