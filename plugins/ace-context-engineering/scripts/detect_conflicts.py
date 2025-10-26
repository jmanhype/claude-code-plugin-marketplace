#!/usr/bin/env python3
# .claude/skills/ace-context-engineering/scripts/detect_conflicts.py
# Purpose: Heuristic conflict detection across bullets to surface contradictions early

import json
import sys
import pathlib
import itertools

# Polarity keywords
NEG = {"never", "avoid", "do not", "don't", "not recommended", "anti-pattern"}
POS = {"always", "must", "do", "recommended", "should", "best practice"}

def load(p):
    """Load JSON file"""
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))

def polarity(text):
    """Detect positive/negative polarity in text"""
    tl = text.lower()
    has_neg = any(x in tl for x in NEG)
    has_pos = any(x in tl for x in POS)
    return (has_pos, has_neg)

def main():
    if len(sys.argv) != 3:
        print("Usage: detect_conflicts.py <bullets.json> <out_report.json>")
        sys.exit(2)

    bullets = load(sys.argv[1])
    report = []

    print(f"🔍 Checking {len(bullets)} bullets for conflicts...")

    for a, b in itertools.combinations(bullets, 2):
        # Require shared tags for meaningful comparison
        shared_tags = set(a.get("tags", [])) & set(b.get("tags", []))
        if not shared_tags:
            continue

        # Check polarity mismatch
        ap, an = polarity(a.get("content", ""))
        bp, bn = polarity(b.get("content", ""))

        if (ap and bn) or (an and bp):
            report.append({
                "a_id": a["id"],
                "b_id": b["id"],
                "shared_tags": sorted(list(shared_tags)),
                "a_excerpt": a["content"][:180] + "...",
                "b_excerpt": b["content"][:180] + "...",
                "note": "Potential contradiction by polarity keywords"
            })

    pathlib.Path(sys.argv[2]).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"✅ Found {len(report)} potential conflicts → {sys.argv[2]}")

if __name__ == "__main__":
    main()
