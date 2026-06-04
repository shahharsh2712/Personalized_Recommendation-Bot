#!/bin/bash
# Oracle Cloud Always Free — one-command setup after clone + .env
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "Create .env first: cp .env.example .env && nano .env"
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Installing Docker..."
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker "$USER" || true
  echo "Log out and back in, then run: bash deploy/oracle-setup.sh"
  exit 0
fi

COMPOSE_FILES="-f docker-compose.yml -f docker-compose.oracle.yml -f docker-compose.prod.yml"

# Optional: use Atlas if MONGODB_URI contains mongodb+srv
if grep -q 'mongodb+srv' .env 2>/dev/null; then
  COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.atlas.yml"
  SERVICES="ollama web caddy"
  echo "Using MongoDB Atlas from .env"
else
  SERVICES="mongo ollama web caddy"
  echo "Using Docker MongoDB"
fi

if grep -q 'YOUR_DOMAIN.com' deploy/Caddyfile 2>/dev/null; then
  cp deploy/Caddyfile.ip deploy/Caddyfile
fi

echo "Building and starting ($SERVICES)..."
docker compose $COMPOSE_FILES up -d --build $SERVICES

echo "Pulling embedding model (first time, ~5 min)..."
docker compose $COMPOSE_FILES exec -T ollama ollama pull nomic-embed-text

if [ -d data_store ] && [ "$(ls -A data_store/*.json 2>/dev/null | wc -l)" -gt 0 ]; then
  echo "Indexing products..."
  docker compose $COMPOSE_FILES exec -T web python reembed_with_ollama.py || true
fi

PUBLIC_IP=$(curl -s --max-time 5 ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')
echo ""
echo "============================================"
echo "  App URL: http://${PUBLIC_IP}"
echo "  Sign up, complete profile, use dashboard"
echo "============================================"
echo "Logs: docker compose $COMPOSE_FILES logs -f web"
