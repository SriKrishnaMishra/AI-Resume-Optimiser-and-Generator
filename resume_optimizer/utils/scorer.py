from __future__ import annotations
from pathlib import Path
import re
from typing import Dict, Iterable, Set, Tuple

from .semantic import semantic_similarity

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_+#\.\-/]*")


def _tokenize(text: str) -> Set[str]:
    return {t.lower() for t in _WORD_RE.findall(text)}


def load_keywords(directory: Path) -> Dict[str, Set[str]]:
    """
    Load keywords grouped by category (filename stem -> category name).
    Returns a dict: {category: {keywords}}
    """
    categories: Dict[str, Set[str]] = {}
    if directory.exists() and directory.is_dir():
        for p in sorted(directory.glob("*.txt")):
            try:
                cat = p.stem.replace("_", " ").title()
                words: Set[str] = set()
                for line in p.read_text(encoding="utf-8").splitlines():
                    w = line.strip().lower()
                    if w:
                        words.add(w)
                if words:
                    categories[cat] = words
            except Exception:
                continue
    if not categories:
        categories = {
            "General": {
                "python", "java", "javascript", "sql", "aws", "azure", "gcp",
                "docker", "kubernetes", "microservices", "rest", "graphql",
                "machine learning", "nlp", "cv", "mlops", "pandas",
                "numpy", "scikit-learn", "tensorflow", "pytorch",
                "communication", "leadership", "agile", "scrum",
            }
        }
    return categories


def score_text(resume_text: str, job_desc: str, keywords_by_cat: Dict[str, Set[str]]):
    """
    Returns (overall_score, matched_keywords, missing_keywords, details_dict)
    details = {
      'exact_score': float 0..100,
      'semantic': float 0..100,
      'category_breakdown': {cat: {"coverage": %, "matched": set, "missing": set}}
    }
    """
    res_tokens = _tokenize(resume_text)
    jd_tokens = _tokenize(job_desc)

    # Build JD-focused keyword set and per-category stats
    union_all: Set[str] = set().union(*keywords_by_cat.values()) if keywords_by_cat else set()
    jd_kw = union_all.intersection(jd_tokens) or union_all

    matched = jd_kw.intersection(res_tokens)
    missing = jd_kw.difference(res_tokens)

    denom = max(1, len(jd_kw))
    exact_score = 100.0 * len(matched) / denom

    # Category coverage
    cat_breakdown: Dict[str, Dict[str, object]] = {}
    for cat, kws in keywords_by_cat.items():
        cat_focus = kws.intersection(jd_kw) or kws
        cat_matched = res_tokens.intersection(cat_focus)
        cat_missing = cat_focus.difference(res_tokens)
        denom_c = max(1, len(cat_focus))
        coverage = 100.0 * len(cat_matched) / denom_c
        cat_breakdown[cat] = {
            "coverage": coverage,
            "matched": cat_matched,
            "missing": cat_missing,
        }

    # Semantic similarity (TF-IDF cosine) scaled to 0..100
    try:
        sem = semantic_similarity(resume_text, job_desc) * 100.0
    except Exception:
        sem = 0.0

    # Blend score: emphasize exact matches but include semantics
    overall = round(0.7 * exact_score + 0.3 * sem, 1)

    details = {
        "exact_score": round(exact_score, 1),
        "semantic": round(sem, 1),
        "category_breakdown": cat_breakdown,
    }
    return overall, matched, missing, details
