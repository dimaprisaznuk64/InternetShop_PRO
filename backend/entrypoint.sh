#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
until python -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.connect(('postgres', 5432))
    s.close()
    print('PostgreSQL is ready!')
except:
    exit(1)
" 2>/dev/null; do
    echo "PostgreSQL is unavailable — sleeping"
    sleep 2
done

echo "Running migrations..."
alembic upgrade head

echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
