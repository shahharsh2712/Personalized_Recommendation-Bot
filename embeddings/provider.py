"""Unified embedding generation: Ollama (free/local) or OpenAI."""
import logging
import os

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

PROVIDER = (os.getenv("EMBEDDING_PROVIDER") or "ollama").lower()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")


def generate_embedding(text):
    """Return an embedding vector for the given text, or None on failure."""
    if not text or not str(text).strip():
        return None

    if PROVIDER in ("none", "disabled") or os.getenv("LIGHTWEIGHT_DEPLOY") == "1":
        return None

    try:
        if PROVIDER == "openai":
            return _openai_embedding(text)
        return _ollama_embedding(text)
    except Exception as e:
        logger.error("Embedding failed (%s): %s", PROVIDER, e)
        return None


def _ollama_embedding(text):
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/embed",
        json={"model": OLLAMA_EMBED_MODEL, "input": text},
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()
    embeddings = data.get("embeddings") or []
    if not embeddings:
        raise ValueError("Ollama returned empty embeddings")
    return embeddings[0]


def _openai_embedding(text):
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.embeddings.create(model=OPENAI_EMBED_MODEL, input=text)
    return response.data[0].embedding
