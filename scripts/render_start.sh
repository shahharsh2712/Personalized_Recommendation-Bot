#!/bin/sh
set -e
cd "$(dirname "$0")/.."
export PYTHONPATH="${PWD}/src:${PWD}"
cd src
python -c "from setup_frontend_data import ensure_vector_store; ensure_vector_store()"
PORT="${PORT:-5000}"
exec gunicorn wsgi:app --bind "0.0.0.0:${PORT}" --workers 1 --threads 2 --timeout 120
