#!/bin/bash
# LearnHub LMS — FastAPI backend launcher (modular monolith)
cd "$(dirname "$0")"

PY=python3

# Idempotent dependency install (first run only)
if [ ! -f .deps_ok ]; then
  echo "[lms-api] Installing Python dependencies..."
  $PY -m pip install -r requirements.txt --quiet 2>&1 | tail -2
  touch .deps_ok
  echo "[lms-api] Dependencies ready."
fi

echo "[lms-api] Starting FastAPI on 127.0.0.1:8000 ..."
exec $PY -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level info
