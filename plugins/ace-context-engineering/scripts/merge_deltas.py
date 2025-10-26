#!/usr/bin/env python3
# .claude/skills/ace-context-engineering/scripts/merge_deltas.py
# Purpose: Deterministically apply an ACE delta to bullets.json without collapsing detail

import json
import sys
import pathlib
import datetime

def load(p):
    """Load JSON file"""
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))

def dump(p, data):
    """Save JSON file with formatting"""
    pathlib.Path(p).write_text(json.dumps(data, indent=2), encoding="utf-8")

def now():
    """Get current timestamp"""
    return datetime.datetime.utcnow().isoformat() + "Z"

def apply_new(bullets, new_bullets):
    """Add new bullets, checking for ID conflicts"""
    ids = {b["id"] for b in bullets}
    for b in new_bullets:
        if b["id"] in ids:
            raise ValueError(f"Duplicate bullet ID: {b['id']}")
        bullets.append(b)
    print(f"  ✅ Added {len(new_bullets)} new bullets")

def apply_edits(bullets, edits):
    """Apply edits to existing bullets"""
    byid = {b["id"]: b for b in bullets}
    for e in edits:
        b = byid.get(e["id"])
        if not b:
            raise ValueError(f"Edit target not found: {e['id']}")
        for k, v in e["set"].items():
            b[k] = v
        b["last_updated"] = now()
    print(f"  ✅ Applied {len(edits)} edits")

def apply_merges(bullets, merges):
    """Merge bullets while preserving content"""
    byid = {b["id"]: b for b in bullets}
    for m in merges:
        keep = byid.get(m["keep_id"])
        if not keep:
            raise ValueError(f"Merge keep_id not found: {m['keep_id']}")

        for mid in m["merge_ids"]:
            if mid == m["keep_id"]:
                continue
            other = byid.get(mid)
            if not other:
                continue

            # Merge tags and prerequisites
            keep["tags"] = sorted(list(set(keep.get("tags", []) + other.get("tags", []))))
            keep["prerequisites"] = sorted(list(set(keep.get("prerequisites", []) + other.get("prerequisites", []))))

            # Merge counters
            keep["helpful_count"] = keep.get("helpful_count", 0) + other.get("helpful_count", 0)
            keep["harmful_count"] = keep.get("harmful_count", 0) + other.get("harmful_count", 0)

            # Append merged content
            keep["content"] += f"\n\n[Merged from {mid}]: {other.get('content', '')}"

            # Mark other as merged
            other["tags"] = list(set(other.get("tags", []) + ["merged"]))

        keep["last_updated"] = now()
    print(f"  ✅ Merged {len(merges)} bullet groups")

def apply_deprecations(bullets, deprecations):
    """Deprecate bullets by tagging and annotating"""
    byid = {b["id"]: b for b in bullets}
    for d in deprecations:
        b = byid.get(d["id"])
        if not b:
            continue
        b["tags"] = list(set(b.get("tags", []) + ["deprecated"]))
        b["content"] += f"\n\n[Deprecated]: {d['reason']}"
        b["last_updated"] = now()
    print(f"  ✅ Deprecated {len(deprecations)} bullets")

def apply_counters(bullets, counters):
    """Update helpful/harmful counters"""
    byid = {b["id"]: b for b in bullets}
    for c in counters:
        b = byid.get(c["id"])
        if not b:
            continue
        b["helpful_count"] = b.get("helpful_count", 0) + int(c.get("helpful_delta", 0))
        b["harmful_count"] = b.get("harmful_count", 0) + int(c.get("harmful_delta", 0))
        b["last_updated"] = now()
    print(f"  ✅ Updated {len(counters)} counters")

def main():
    if len(sys.argv) != 4:
        print("Usage: merge_deltas.py <bullets.json> <delta.json> <out.json>")
        sys.exit(2)

    data = load(sys.argv[1])
    # Handle both direct list and nested structure
    is_nested = isinstance(data, dict) and "bullets" in data
    bullets = data["bullets"] if is_nested else data
    delta = load(sys.argv[2])

    print(f"📝 Merging delta into {len(bullets)} bullets...")

    # Apply operations in order
    apply_new(bullets, delta.get("new_bullets", []))
    apply_edits(bullets, delta.get("edits", []))
    apply_merges(bullets, delta.get("merges", []))
    apply_deprecations(bullets, delta.get("deprecations", []))
    apply_counters(bullets, delta.get("counters", []))

    # Preserve nested structure if it existed
    if is_nested:
        data["bullets"] = bullets
        data["last_updated"] = now()
        if "metadata" in data:
            data["metadata"]["total_bullets"] = len(bullets)
            data["metadata"]["last_curated"] = now()
        dump(sys.argv[3], data)
    else:
        dump(sys.argv[3], bullets)
    print(f"✅ Merged → {sys.argv[3]} ({len(bullets)} total bullets)")

if __name__ == "__main__":
    main()
