#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "[FireSight] Starting backend..."
cd "$ROOT/backend"
python app.py &
BACKEND_PID=$!

echo "[FireSight] Starting frontend..."
cd "$ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

echo "[FireSight] Both servers running. Press Ctrl+C to stop."

trap "echo ''; echo '[FireSight] Shutting down...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM

wait
