#!/bin/sh
# Run once after first deploy: docker compose run --rm ollama-init
set -e
ollama pull "${OLLAMA_EMBED_MODEL:-nomic-embed-text}"
echo "Model ready."
