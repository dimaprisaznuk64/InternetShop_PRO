#!/bin/bash
set -euo pipefail

echo "=== InternetShop PRO — Local Frontend Build ==="

cd "$(dirname "$0")/../frontend"

echo "[1/4] Installing dependencies..."
npm ci --ignore-scripts

echo "[2/4] Running tests..."
npm test || echo "WARN: Some tests failed, continuing build..."

echo "[3/4] Linting..."
npm run lint || echo "WARN: Lint warnings found, continuing build..."

echo "[4/4] Building production bundle..."
npm run build

echo "=== Build complete! ==="
echo "Output: $(pwd)/dist/"
du -sh dist/
