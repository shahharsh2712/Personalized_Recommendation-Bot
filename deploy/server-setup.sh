#!/bin/bash
# Run on Ubuntu VPS after git clone. Usage: bash deploy/server-setup.sh
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "Copy .env.example to .env and fill in secrets first."
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker "$USER" || true
  echo "Log out and back in, then re-run this script."
  exit 0
fi

# IP-only HTTP unless you edited deploy/Caddyfile with your domain
if grep -q 'YOUR_DOMAIN.com' deploy/Caddyfile 2>/dev/null; then
  cp deploy/Caddyfile.ip deploy/Caddyfile
  echo "Using IP-only Caddyfile (port 80). Set your domain in deploy/Caddyfile for HTTPS."
fi

docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

echo "Pulling embedding model (first time, may take a few minutes)..."
docker compose exec -T ollama ollama pull nomic-embed-text

echo ""
echo "Done. Open: http://$(curl -s ifconfig.me 2>/dev/null || echo YOUR_SERVER_IP)"
echo "Optional: docker compose exec web python reembed_with_ollama.py"
