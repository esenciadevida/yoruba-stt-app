"""Build the RAG few-shot translation index for Bámi-Sọ̀rọ̀.

Downloads the Masakhane MAFAND parallel corpus, cleans it, embeds both the
English and Yoruba sides with paraphrase-multilingual-MiniLM-L12-v2, and
writes the index under models/rag/ for common.translation_rag to consume.

Usage:
    venv\\Scripts\\python.exe scripts\\build_rag_index.py
"""

import os
import sys
import json
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

INDEX_DIR = os.path.join(ROOT, "models", "rag")

# Primary corpus: Masakhane mafand (news/general domain, high quality).
MAFAND = {"name": "masakhane/mafand", "config": "en-yor", "splits": ("train", "validation")}
# Fallback corpus: Opus-100 (larger but dominated by short UI strings).
OPUS = {"name": "Helsinki-NLP/opus-100", "config": "en-yo", "splits": ("train",)}
# Multilingual model for better Yoruba-side retrieval
EMBED_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

MAX_PAIRS = 12000
MAX_SRC_CHARS = 400
MIN_SRC_CHARS = 3


def _clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_pair(row):
    """Extract (en, yo) from a mafand/opus row regardless of schema."""
    t = row.get("translation") or row
    if isinstance(t, dict):
        en = t.get("en") or t.get("source") or row.get("en") or row.get("source")
        yo = t.get("yo") or t.get("yor") or t.get("target") or row.get("yo") or row.get("target")
    else:
        en = row.get("en") or row.get("source")
        yo = row.get("yo") or row.get("yor") or row.get("target")
    return _clean(str(en or "")), _clean(str(yo or ""))


def _load_pairs():
    from datasets import load_dataset

    for corpus in (MAFAND, OPUS):
        try:
            rows = []
            for split in corpus["splits"]:
                rows.extend(load_dataset(corpus["name"], corpus["config"], split=split))
            print(f"Loading {corpus['name']} ({corpus['config']}) -> {len(rows)} raw rows")
            return corpus["name"], rows
        except Exception as e:
            print(f"  skipped {corpus['name']}: {type(e).__name__}: {str(e)[:90]}")
    raise SystemExit("No usable parallel corpus found.")


def main():
    from sentence_transformers import SentenceTransformer

    os.makedirs(INDEX_DIR, exist_ok=True)

    dataset_name, ds = _load_pairs()

    pairs, seen = [], set()
    for row in ds:
        en, yo = _extract_pair(row)
        if not en or not yo:
            continue
        if len(en) < MIN_SRC_CHARS or len(en) > MAX_SRC_CHARS:
            continue
        if en.lower() == yo.lower():
            continue  # not a real translation (e.g. proper-name lists)
        key = en.lower() + "\x00" + yo.lower()
        if key in seen:
            continue
        seen.add(key)
        pairs.append({"en": en, "yo": yo})
        if len(pairs) >= MAX_PAIRS:
            break

    print(f"Using {len(pairs)} cleaned parallel pairs")

    print(f"Loading embedding model {EMBED_MODEL_NAME}...")
    model = SentenceTransformer(EMBED_MODEL_NAME)

    en_texts = [p["en"] for p in pairs]
    yo_texts = [p["yo"] for p in pairs]

    print("Embedding English side...")
    emb_en = model.encode(en_texts, batch_size=64, normalize_embeddings=True, show_progress_bar=True)
    print("Embedding Yoruba side...")
    emb_yo = model.encode(yo_texts, batch_size=64, normalize_embeddings=True, show_progress_bar=True)

    pairs_path = os.path.join(INDEX_DIR, "pairs.json")
    with open(pairs_path, "w", encoding="utf-8") as f:
        json.dump(pairs, f, ensure_ascii=False)

    import numpy as np
    np.save(os.path.join(INDEX_DIR, "emb_en.npy"), np.asarray(emb_en, dtype=np.float32))
    np.save(os.path.join(INDEX_DIR, "emb_yo.npy"), np.asarray(emb_yo, dtype=np.float32))

    with open(os.path.join(INDEX_DIR, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "source": dataset_name,
                "pairs": len(pairs),
                "embedder": EMBED_MODEL_NAME,
            },
            f,
            indent=2,
        )

    print(f"Done. Index written to {INDEX_DIR}")


if __name__ == "__main__":
    main()
