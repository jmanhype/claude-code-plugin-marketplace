<!-- .claude/context/context.md -->
<!-- Purpose: Concise context system hub with progressive disclosure -->

# Context

## Context System Structure

Filesystem-based, progressive disclosure. Start here, then read the three files below before non-trivial work.

```
.claude/
├── context/
│   ├── memory/
│   │   ├── CLAUDE.md        # retrieval, counters, bullets.json layout
│   │   ├── bullets.json     # authoritative bullet library (seeded)
│   │   ├── ratings.jsonl    # user feedback (optional)
│   │   └── ratings.md       # rating interface guide
│   ├── projects/CLAUDE.md   # project index
│   ├── tools/CLAUDE.md      # tools/skills/MCP overview
│   └── context.md           # (this file)
├── skills/
│   └── ace-context-engineering/
│       ├── skill.md         # ACE skill definition
│       ├── schemas/         # JSON schemas
│       └── scripts/         # Python tools
└── docs/
    └── walkthroughs/        # End-to-end examples
```

---

## MANDATORY ACTION

Read next, in order:

1. `.claude/context/memory/CLAUDE.md`
2. `.claude/context/projects/CLAUDE.md`
3. `.claude/context/tools/CLAUDE.md`

---

## Change Policy

- Propose **ACE delta** changes; avoid monolithic rewrites
- Use `skills/ace-context-engineering/scripts/validate_delta.py` before merge
- Run `merge_deltas.py` to apply changes
- Run `detect_conflicts.py` to check contradictions

---

## Quick Commands

```bash
# Retrieve bullets for a task
python scripts/retrieve_bullets.py bullets.json "create thumbnail" --tags yt.thumbnail --topk 5

# Validate delta
python scripts/validate_delta.py delta proposed_delta.json

# Merge delta
python scripts/merge_deltas.py bullets.json delta.json bullets_updated.json

# Update counters
python scripts/update_counters.py bullets.json gen_output.json --ratings ratings.jsonl

# Detect conflicts
python scripts/detect_conflicts.py bullets.json conflicts_report.json
```

---

## Attribution

ACE concepts from Zhang et al., 2025 (arXiv:2510.04618, **CC BY 4.0**).
