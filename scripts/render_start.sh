#!/bin/sh
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="${ROOT}/src:${ROOT}"
cd "${ROOT}/src"
python -c "from setup_frontend_data import ensure_vector_store; ensure_vector_store()"
PORT="${PORT:-5000}"
exec gunicorn wsgi:app --bind "0.0.0.0:${PORT}" --workers 1 --threads 2 --timeout 120
