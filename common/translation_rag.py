"""Retrieval-augmented few-shot translation support.

Indexes a parallel English-Yoruba corpus with the sentence-transformers
paraphrase-multilingual-MiniLM-L12-v2 model. At translation time we embed
the input and retrieve the most similar source sentences so their reference
translations can be injected as few-shot examples into the GPT prompt.
This measurably improves accuracy and consistency, especially for idiomatic
Yoruba and common conversational patterns.

Runtime is designed to degrade gracefully: if the index or embedding model
is unavailable, callers get an empty example list and translation continues
normally.
"""

import os
import json
import logging

import numpy as np

logger = logging.getLogger(__name__)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_DIR = os.path.join(ROOT, "models", "rag")
# Multilingual model for better Yoruba-side retrieval
EMBED_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

_CACHE = {"embedder": None, "index": None}


def _load_embedder():
    if _CACHE["embedder"] is None:
        try:
            from sentence_transformers import SentenceTransformer

            _CACHE["embedder"] = SentenceTransformer(EMBED_MODEL_NAME)
        except Exception as e:
            logger.warning("RAG embedder unavailable: %s", e)
            _CACHE["embedder"] = False
    return _CACHE["embedder"] or None


def _load_index():
    """Load the prebuilt index, or None if not present/broken."""
    if _CACHE["index"] is None:
        pairs_path = os.path.join(INDEX_DIR, "pairs.json")
        emb_en_path = os.path.join(INDEX_DIR, "emb_en.npy")
        emb_yo_path = os.path.join(INDEX_DIR, "emb_yo.npy")
        if not all(os.path.exists(p) for p in (pairs_path, emb_en_path, emb_yo_path)):
            _CACHE["index"] = False
            return None
        try:
            with open(pairs_path, "r", encoding="utf-8") as f:
                pairs = json.load(f)
            _CACHE["index"] = {
                "pairs": pairs,
                "emb_en": np.load(emb_en_path),
                "emb_yo": np.load(emb_yo_path),
            }
        except Exception as e:
            logger.warning("RAG index failed to load: %s", e)
            _CACHE["index"] = False
            return None
    return _CACHE["index"] or None


def is_available() -> bool:
    return _load_index() is not None


def _top_k(emb: np.ndarray, query_vec: np.ndarray, k: int) -> list[int]:
    sims = np.dot(emb, query_vec)  # both L2-normalized -> cosine similarity
    top = np.argsort(sims)[::-1][:k]
    return [int(i) for i in top]


def get_few_shot_examples(text: str, direction: str, k: int = 3) -> list[tuple[str, str]]:
    """Return up to ``k`` (source, target) reference pairs similar to ``text``.

    ``direction`` is "en2yo" or "yo2en". Returns [] when RAG is unavailable.
    """
    if not text or not text.strip():
        return []

    index = _load_index()
    embedder = _load_embedder()
    if index is None or embedder is None:
        return []

    try:
        query_vec = embedder.encode([text.strip()], normalize_embeddings=True)[0]
        if direction == "en2yo":
            idxs = _top_k(index["emb_en"], query_vec, k)
        else:
            idxs = _top_k(index["emb_yo"], query_vec, k)
    except Exception as e:
        logger.warning("RAG retrieval failed: %s", e)
        return []

    examples = []
    seen = set()
    for i in idxs:
        src = (index["pairs"][i] or {}).get("en", "").strip()
        tgt = (index["pairs"][i] or {}).get("yo", "").strip()
        if not src or not tgt or src.lower() == tgt.lower():
            continue
        if src.lower() in seen:
            continue
        seen.add(src.lower())
        examples.append((src[:160], tgt[:160]))
    return examples
