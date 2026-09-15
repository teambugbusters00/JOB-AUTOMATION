#!/bin/sh
set -eu

/opt/venv/bin/uvicorn web.app:app --host 127.0.0.1 --port 8000 &
PY_PID=$!

cleanup() {
  kill "$PY_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

exec npm run start:web
