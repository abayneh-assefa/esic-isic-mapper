# File: embedding_utils.py

import os
import yaml
import requests
import numpy as np
from dotenv import load_dotenv

# ─── Load Config and Defaults ───────────────────────────
load_dotenv()
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

OLLAMA_HOST      = os.getenv("OLLAMA_HOST", config.get("ollama_host", "http://localhost:11434"))
DEFAULT_MODEL    = os.getenv("EMBEDDING_MODEL", config.get("embedding_model", "nomic-embed-text"))
DEFAULT_DIM      = config["embedding"].get("dimension", 768)
DEFAULT_NORMMODE = os.getenv("NORMALIZE_MODE", config["embedding"].get("normalization_mode", "cosine"))
VERBOSE          = os.getenv("EMBED_VERBOSE", "false").lower() == "true"

# ─── HTTP Session for Connection Reuse ──────────────────
session = requests.Session()
session.headers.update({"Connection": "keep-alive"})

# ─── Normalize Embedding Vector ─────────────────────────
def normalize_vector(vec, mode="cosine"):
    vec = np.asarray(vec, dtype=np.float32)
    # print(mode)
    # print(vec[:4])
    if mode in ("cosine", "dotProduct"):
        norm = np.linalg.norm(vec)
        return (vec / norm).tolist() if norm > 0 else vec.tolist()
    return vec.tolist()

# ─── Embedding with Optional Normalization ──────────────
def get_embedding(text: str, model: str = None, normalize_mode: str = None):
    model     = model or DEFAULT_MODEL
    norm_mode = normalize_mode or DEFAULT_NORMMODE
    endpoint  = f"{OLLAMA_HOST}/api/embeddings"

    try:
        response = session.post(endpoint, json={"model": model, "prompt": text}, timeout=20)
        response.raise_for_status()
        data = response.json()

        vec = data.get("embedding")
        if not vec:
            print(f"❌ Missing embedding for '{text[:60]}'...") if VERBOSE else None
            return [0.0] * DEFAULT_DIM

        vec = [float(v) for v in vec]
        return normalize_vector(vec, norm_mode)

    except Exception as e:
        print(f"❌ Embedding error: {e}") if VERBOSE else None
        return [0.0] * DEFAULT_DIM

# ─── All Normalization Modes (raw, cosine, dotProduct) ──
def get_all_embeddings(text: str, model: str = None):
    model    = model or DEFAULT_MODEL
    endpoint = f"{OLLAMA_HOST}/api/embeddings"

    # print(text)
    # print(model)


    try:
        response = session.post(endpoint, json={"model": model, "prompt": text}, timeout=20)
        response.raise_for_status()
        data = response.json()

        vec = data.get("embedding")
        if not vec:
            print(f"❌ Missing embedding vector.") if VERBOSE else None
            fallback = [0.0] * DEFAULT_DIM
            return {
                f"embedding_raw_{model}": fallback,
                f"embedding_cosine_{model}": fallback,
                f"embedding_dot_{model}": fallback
            }

        raw = [float(v) for v in vec]
        return {
            f"embedding_raw_{model}": normalize_vector(raw, mode="none"),
            f"embedding_cosine_{model}": normalize_vector(raw, mode="cosine"),
            f"embedding_dot_{model}": normalize_vector(raw, mode="dotProduct")
        }

    except Exception as e:
        print(f"❌ Embedding batch error: {e}") if VERBOSE else None
        fallback = [0.0] * DEFAULT_DIM
        return {
            f"embedding_raw_{model}": fallback,
            f"embedding_cosine_{model}": fallback,
            f"embedding_dot_{model}": fallback
        }

