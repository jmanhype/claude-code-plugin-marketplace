#!/usr/bin/env python3
# .claude/skills/ace-context-engineering/scripts/update_counters.py
# Purpose: Integrate execution and human feedback into bullet counters

import json
import sys
import pathlib

def load(p):
    """Load JSON file"""
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))

def apply_gen(bullets, gen):
    """Apply generator output to counters"""
    used = set(gen.get("used_bullet_ids", []))
    bc = gen.get("bullet_confidence", {})

    for b in bullets:
        if b["id"] in used:
            # Weight by confidence; floor at +1
            inc = max(1, int(round(bc.get(b["id"], 0.5) * 2)))
            b["helpful_count"] = b.get("helpful_count", 0) + inc

    print(f"  ✅ Updated {len(used)} bullets from generator output")

def apply_ratings(bullets, ratings_path):
    """Apply user ratings from JSONL file"""
    if not ratings_path:
        return

    path = pathlib.Path(ratings_path)
    if not path.exists():
        print(f"  ⚠️  Ratings file not found: {ratings_path}")
        return

    byid = {b["id"]: b for b in bullets}
    count = 0

    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        ev = json.loads(line)
        b = byid.get(ev["bullet_id"])
        if not b:
            continue

        if ev["value"] > 0:
            b["helpful_count"] = b.get("helpful_count", 0) + ev["value"]
        elif ev["value"] < 0:
            b["harmful_count"] = b.get("harmful_count", 0) + abs(ev["value"])

        count += 1

    print(f"  ✅ Applied {count} ratings from {ratings_path}")

def main():
    if len(sys.argv) < 3:
        print("Usage: update_counters.py <bullets.json> <generator_output.json> [--ratings ratings.jsonl] [--out out.json]")
        sys.exit(2)

    bullets = load(sys.argv[1])
    gen = load(sys.argv[2])

    ratings = None
    out = sys.argv[1]

    for i, a in enumerate(sys.argv):
        if a == "--ratings" and i + 1 < len(sys.argv):
            ratings = sys.argv[i + 1]
        if a == "--out" and i + 1 < len(sys.argv):
            out = sys.argv[i + 1]

    print(f"📝 Updating counters for {len(bullets)} bullets...")
    apply_gen(bullets, gen)
    apply_ratings(bullets, ratings)

    pathlib.Path(out).write_text(json.dumps(bullets, indent=2), encoding="utf-8")
    print(f"✅ Counters updated → {out}")

if __name__ == "__main__":
    main()
