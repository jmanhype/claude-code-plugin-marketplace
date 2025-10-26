#!/usr/bin/env python3
# .claude/skills/ace-context-engineering/scripts/retrieve_bullets.py
# Purpose: Rank bullets for a query using tags + TF-IDF cosine + helpfulness prior

import json
import math
import sys
import pathlib
import re
from collections import Counter

def tokenize(s):
    """Extract alphanumeric tokens from string"""
    return re.findall(r"[a-z0-9]+", s.lower())

def build_idf(docs):
    """Build IDF (Inverse Document Frequency) from documents"""
    df = Counter()
    for d in docs:
        toks = set(tokenize(d))
        df.update(toks)
    N = len(docs)
    return {t: math.log((N + 1) / (c + 1)) + 1 for t, c in df.items()}

def tfidf_vec(text, idf):
    """Compute TF-IDF vector for text"""
    tf = Counter(tokenize(text))
    return {t: (tf[t] * idf.get(t, 0.0)) for t in tf}

def cosine(a, b):
    """Compute cosine similarity between two vectors"""
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in set(a) | set(b))
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return 0.0 if na == 0 or nb == 0 else dot / (na * nb)

def score(bullet, qvec, idf, qtags):
    """
    Score bullet for query using:
    2.0 * tag_overlap + cosine(TF-IDF) + 0.1 * log1p(helpful - harmful)
    """
    tags = set(bullet.get("tags", []))
    tag_overlap = len(tags & qtags)

    text = bullet.get("title", "") + " " + bullet.get("content", "")
    bvec = tfidf_vec(text, idf)
    cos = cosine(qvec, bvec)

    helpful = bullet.get("helpful_count", 0)
    harmful = bullet.get("harmful_count", 0)
    prior = math.log1p(max(0, helpful - harmful)) * 0.1

    return 2.0 * tag_overlap + cos + prior

def main():
    if len(sys.argv) < 3:
        print("Usage: retrieve_bullets.py <bullets.json> <query> [--tags t1,t2] [--topk 10]")
        sys.exit(2)

    data = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    # Handle both direct list and nested structure
    bullets = data.get("bullets", data) if isinstance(data, dict) else data
    query = sys.argv[2]

    # Parse optional arguments
    tags = set()
    topk = 10
    for i, a in enumerate(sys.argv):
        if a == "--tags" and i + 1 < len(sys.argv):
            tags = set(sys.argv[i + 1].split(","))
        if a == "--topk" and i + 1 < len(sys.argv):
            topk = int(sys.argv[i + 1])

    # Build IDF from all bullets + query
    docs = [(b["title"] + " " + b["content"]) for b in bullets]
    idf = build_idf(docs + [query])
    qvec = tfidf_vec(query, idf)

    # Score and rank bullets
    scored = sorted(
        bullets,
        key=lambda b: score(b, qvec, idf, tags),
        reverse=True
    )[:topk]

    # Output top-K with scores
    result = [
        {
            "id": b["id"],
            "title": b["title"],
            "score": round(score(b, qvec, idf, tags), 4),
            "tags": b.get("tags", []),
            "confidence": b.get("confidence", 0.5)
        }
        for b in scored
    ]

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
