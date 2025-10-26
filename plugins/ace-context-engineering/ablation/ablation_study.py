#!/usr/bin/env python3
"""
ACE Ablation Study: Systematically remove components to measure their contribution.

Tests:
1. Full ACE (baseline)
2. No TF-IDF (tags only)
3. No tags (TF-IDF only)
4. No feedback counters (helpful/harmful)
5. No conflict detection
6. Random retrieval (control)
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Set
import math
import re
from collections import Counter
import random


def load_playbook(path: Path) -> List[Dict]:
    """Load bullets from playbook."""
    with open(path) as f:
        data = json.load(f)
    return data.get("bullets", data)


def tokenize(text: str) -> List[str]:
    """Extract tokens."""
    return re.findall(r"[a-z0-9]+", text.lower())


def build_idf(docs: List[str]) -> Dict[str, float]:
    """Build IDF."""
    df = Counter()
    for doc in docs:
        df.update(set(tokenize(doc)))
    N = len(docs)
    return {t: math.log((N + 1) / (c + 1)) + 1 for t, c in df.items()}


def tfidf_vector(text: str, idf: Dict[str, float]) -> Dict[str, float]:
    """Compute TF-IDF vector."""
    tf = Counter(tokenize(text))
    return {t: tf[t] * idf.get(t, 0.0) for t in tf}


def cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
    """Cosine similarity."""
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in set(a) | set(b))
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return 0.0 if na == 0 or nb == 0 else dot / (na * nb)


# === Ablation Variants ===

def score_full_ace(bullet: Dict, qvec: Dict[str, float], idf: Dict[str, float], qtags: Set[str]) -> float:
    """Full ACE: TF-IDF + tags + feedback."""
    tags = set(bullet.get("tags", []))
    tag_overlap = len(tags & qtags)

    text = bullet.get("title", "") + " " + bullet.get("content", "")
    bvec = tfidf_vector(text, idf)
    cos = cosine(qvec, bvec)

    helpful = bullet.get("helpful_count", 0)
    harmful = bullet.get("harmful_count", 0)
    feedback = math.log1p(max(0, helpful - harmful)) * 0.1

    return 2.0 * tag_overlap + cos + feedback


def score_no_tfidf(bullet: Dict, qvec: Dict[str, float], idf: Dict[str, float], qtags: Set[str]) -> float:
    """Tags + feedback only."""
    tags = set(bullet.get("tags", []))
    tag_overlap = len(tags & qtags)

    helpful = bullet.get("helpful_count", 0)
    harmful = bullet.get("harmful_count", 0)
    feedback = math.log1p(max(0, helpful - harmful)) * 0.1

    return 2.0 * tag_overlap + feedback


def score_no_tags(bullet: Dict, qvec: Dict[str, float], idf: Dict[str, float], qtags: Set[str]) -> float:
    """TF-IDF + feedback only."""
    text = bullet.get("title", "") + " " + bullet.get("content", "")
    bvec = tfidf_vector(text, idf)
    cos = cosine(qvec, bvec)

    helpful = bullet.get("helpful_count", 0)
    harmful = bullet.get("harmful_count", 0)
    feedback = math.log1p(max(0, helpful - harmful)) * 0.1

    return cos + feedback


def score_no_feedback(bullet: Dict, qvec: Dict[str, float], idf: Dict[str, float], qtags: Set[str]) -> float:
    """TF-IDF + tags only."""
    tags = set(bullet.get("tags", []))
    tag_overlap = len(tags & qtags)

    text = bullet.get("title", "") + " " + bullet.get("content", "")
    bvec = tfidf_vector(text, idf)
    cos = cosine(qvec, bvec)

    return 2.0 * tag_overlap + cos


def score_random(bullet: Dict, qvec: Dict[str, float], idf: Dict[str, float], qtags: Set[str]) -> float:
    """Random baseline."""
    return random.random()


# === Test Queries ===

TEST_QUERIES = [
    {
        "query": "editing files with validation",
        "tags": ["tool.edit", "validation"],
        "expected_top_3": ["bullet-2025-10-25-001", "bullet-2025-10-25-002", "bullet-2025-10-25-006"]
    },
    {
        "query": "python JSON data processing",
        "tags": ["python", "json"],
        "expected_top_3": ["bullet-2025-10-26-001", "bullet-2025-10-25-006"]
    },
    {
        "query": "git commit workflow",
        "tags": ["tool.bash", "git.commit"],
        "expected_top_3": ["bullet-2025-10-25-011", "bullet-2025-10-25-003"]
    },
    {
        "query": "parallel tool calls performance",
        "tags": ["tool.usage", "performance"],
        "expected_top_3": ["bullet-2025-10-25-007"]
    }
]


def run_ablation(bullets: List[Dict], test_queries: List[Dict]) -> Dict[str, any]:
    """Run ablation study."""

    variants = {
        "Full ACE (baseline)": score_full_ace,
        "No TF-IDF": score_no_tfidf,
        "No Tags": score_no_tags,
        "No Feedback": score_no_feedback,
        "Random (control)": score_random,
    }

    results = {name: {"precision": [], "recall": [], "top1_hits": 0} for name in variants}

    # Build IDF
    docs = [b.get("title", "") + " " + b.get("content", "") for b in bullets]

    for test in test_queries:
        query = test["query"]
        qtags = set(test["tags"])
        expected = set(test["expected_top_3"])

        idf = build_idf(docs + [query])
        qvec = tfidf_vector(query, idf)

        for name, score_fn in variants.items():
            # Rank bullets
            scored = sorted(bullets, key=lambda b: score_fn(b, qvec, idf, qtags), reverse=True)[:3]
            retrieved = {b["id"] for b in scored}

            # Metrics
            hits = len(retrieved & expected)
            precision = hits / 3 if retrieved else 0
            recall = hits / len(expected) if expected else 0

            results[name]["precision"].append(precision)
            results[name]["recall"].append(recall)

            # Top-1 accuracy
            if scored and scored[0]["id"] in expected:
                results[name]["top1_hits"] += 1

    # Aggregate metrics
    for name in variants:
        r = results[name]
        r["avg_precision"] = sum(r["precision"]) / len(r["precision"]) if r["precision"] else 0
        r["avg_recall"] = sum(r["recall"]) / len(r["recall"]) if r["recall"] else 0
        r["top1_accuracy"] = r["top1_hits"] / len(test_queries)
        r["f1"] = 2 * r["avg_precision"] * r["avg_recall"] / (r["avg_precision"] + r["avg_recall"]) if (r["avg_precision"] + r["avg_recall"]) > 0 else 0

    return results


def main():
    playbook_path = Path(__file__).parent.parent / "skills" / "playbook.json"
    bullets = load_playbook(playbook_path)

    print("=" * 60)
    print("ACE ABLATION STUDY")
    print("=" * 60)
    print(f"Playbook: {len(bullets)} bullets")
    print(f"Test queries: {len(TEST_QUERIES)}")
    print()

    results = run_ablation(bullets, TEST_QUERIES)

    print("RESULTS:")
    print("-" * 60)
    print(f"{'Variant':<25} {'Precision':<12} {'Recall':<12} {'F1':<12} {'Top-1 Acc':<12}")
    print("-" * 60)

    for name in ["Full ACE (baseline)", "No TF-IDF", "No Tags", "No Feedback", "Random (control)"]:
        r = results[name]
        print(f"{name:<25} {r['avg_precision']:<12.3f} {r['avg_recall']:<12.3f} {r['f1']:<12.3f} {r['top1_accuracy']:<12.3f}")

    print("-" * 60)
    print()

    # Component contribution analysis
    baseline = results["Full ACE (baseline)"]["f1"]

    print("COMPONENT CONTRIBUTION (F1 drop when removed):")
    print("-" * 60)

    contributions = {
        "TF-IDF": baseline - results["No TF-IDF"]["f1"],
        "Tags": baseline - results["No Tags"]["f1"],
        "Feedback": baseline - results["No Feedback"]["f1"],
    }

    for component, drop in sorted(contributions.items(), key=lambda x: -x[1]):
        pct = (drop / baseline * 100) if baseline > 0 else 0
        print(f"{component:<20} F1 drop: {drop:>6.3f} ({pct:>5.1f}%)")

    print()

    # Save detailed results
    output_path = Path(__file__).parent / "ablation_results.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Detailed results saved to: {output_path}")


if __name__ == "__main__":
    main()
