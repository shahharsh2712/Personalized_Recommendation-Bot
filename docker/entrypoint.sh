#!/bin/sh
set -e

echo "Waiting for MongoDB..."
until python -c "from pymongo import MongoClient; import os; MongoClient(os.environ.get('MONGODB_URI','mongodb://mongo:27017/'), serverSelectionTimeoutMS=2000).admin.command('ping')" 2>/dev/null; do
  sleep 2
done
echo "MongoDB is up."

if [ "${SKIP_OLLAMA_WAIT}" = "1" ]; then
  echo "Skipping Ollama (lightweight deploy — uses pre-built product index)."
else
  OLLAMA_URL="${OLLAMA_BASE_URL:-http://ollama:11434}"
  echo "Waiting for Ollama at ${OLLAMA_URL}..."
  until curl -sf "${OLLAMA_URL}/api/tags" >/dev/null 2>&1; do
    sleep 2
  done
  echo "Ollama is up."
fi

cd /app/src
python -c "from setup_frontend_data import ensure_vector_store; ensure_vector_store()" 2>/dev/null || true

WORKERS="${GUNICORN_WORKERS:-2}"
THREADS="${GUNICORN_THREADS:-4}"

exec gunicorn wsgi:app \
  --bind 0.0.0.0:5000 \
  --workers "$WORKERS" \
  --threads "$THREADS" \
  --timeout 120
