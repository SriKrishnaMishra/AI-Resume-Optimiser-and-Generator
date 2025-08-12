from __future__ import annotations
from functools import lru_cache
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as _cos


@lru_cache(maxsize=64)
def _vectorize_pair(a: str, b: str):
    vec = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
    X = vec.fit_transform([a or "", b or ""])  # 2 x N
    return X


def semantic_similarity(a: str, b: str) -> float:
    """Return cosine similarity in 0..1 between two texts using TF-IDF bigrams."""
    try:
        X = _vectorize_pair(a or "", b or "")
    except Exception:
        # Handles cases like empty vocabulary or unexpected errors
        return 0.0
    try:
        # sklearn returns a dense 1x1 ndarray; index with [0, 0]
        sim = float(_cos(X[0], X[1])[0, 0])
    except Exception:
        return 0.0
    # clamp possible numerical instability
    if sim < 0:
        sim = 0.0
    if sim > 1:
        sim = 1.0
    return float(sim)
