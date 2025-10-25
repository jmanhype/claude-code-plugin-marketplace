<!-- .claude/context/context.md -->
<!-- Purpose: Filesystem-based context hub + ACE (Agentic Context Engineering) policy for progressive disclosure and incremental deltas. -->

# Context

## Context System Structure

The **Context System** is filesystem-based. Use your file tools to navigate and read context efficiently.

- Prefer `Glob` to discover relevant context files; prefer `Grep` (or search) to locate specific guidance or tool docs.
- Load only what you need (progressive disclosure). Start from this file, then follow links.

```
.claude/
├── context/
│   ├── memory/
│   │   └── CLAUDE.md          # memory model, counters, retrieval policy
│   ├── projects/
│   │   └── CLAUDE.md          # project index and navigation
│   ├── tools/
│   │   └── CLAUDE.md          # tools/skills/MCP overview + usage policies
│   └── context.md             # (this file) system overview + mandatory actions
├── skills/
│   └── ace-context-engineering/
│       ├── skill.md           # ACE skill (progressive disclosure)
│       ├── schemas/
│       │   ├── bullet.schema.json   # full bullet schema (optional read)
│       │   └── delta.schema.json    # full delta schema (optional read)
│       └── scripts/
│           └── validate_delta.py    # optional: validate proposed deltas locally
```

> **Tip**: Context is part of the runtime's "contract". Treat it as source-controlled documentation that evolves with tasks.

---

## Managing Context

- **Add** new context by creating Markdown under the relevant directory (memory/projects/tools).
- **Update** context by editing the specific Markdown file; keep diffs small and purposeful.
- **Bias to read**: when unsure, read *before* acting; it's cheaper than incorrect tool use.
- **Propose deltas, not rewrites**: for substantive changes, use ACE-style *delta updates* (see below).
- **Review**: discuss non-trivial changes with the user before merging into persistent context.
- **Keep current**: retire or mark stale guidance; prefer deprecations over deletion if unsure.

---

## MANDATORY ACTION

You **MUST** read the following context files before proceeding on non-trivial work:

1. `.claude/context/memory/CLAUDE.md`
2. `.claude/context/projects/CLAUDE.md`
3. `.claude/context/tools/CLAUDE.md`

**Additional guidance:**

- Always consider which context is relevant and **read the relevant files**.
- **Bias towards reading** context rather than skipping it.
- When facing uncertainty, consult context *first* before proposing solutions.
- Context files contain domain-specific heuristics, common pitfalls, and proven patterns.

---

## ACE Playbook (Agentic Context Engineering)

**Goal:** Adapt **contexts** (not weights) using **itemized bullets** and **incremental deltas** to avoid brevity bias and context collapse.

### Core Rules

1. **No monolithic rewrites.** Only propose *localized* edits via deltas.
2. Preserve **domain-specific detail** (heuristics, edge cases, tool recipes, common failure modes).
3. Keep bullets **atomic** (one purpose each). Split if a bullet grows multi-topic.
4. Prefer lessons grounded in **execution signals** (tool success/failure, validations); tag weak evidence `"low_confidence"`.
5. **Grow steadily, refine deliberately.** Default to adding new bullets; only merge/deprecate when redundancy or obsolescence is clear.

### Bullet (playbook entry) — minimal shape

```json
{
  "id": "string",             // stable unique id (e.g., "bullet-2024-01-15-001")
  "title": "string",          // purpose-centric title
  "content": "string",        // detailed, atomic guidance (no generic fluff)
  "tags": ["string"],         // e.g., ["api.email","xbrl","tool.use","antipattern"]
  "evidence": [
    {
      "type": "string",       // e.g., "execution", "validation", "user_feedback"
      "ref": "string",        // reference (file, commit, task ID)
      "note": "string"        // brief context
    }
  ],
  "helpful_count": 0,         // incremented when bullet aids correct solution
  "harmful_count": 0,         // incremented when bullet misleads
  "last_updated": "ISO-8601", // automatic timestamp
  "links": ["string"]         // related bullets or external docs
}
```

**Key principles:**

- `id` must be stable across updates (enables delta tracking)
- `content` should be **verbose & DRY**: detailed enough to be actionable, without redundancy across bullets
- `tags` enable precise retrieval; use hierarchical notation (e.g., `"tool.bash.retry"`, `"api.github.ratelimit"`)
- `evidence` grounds the bullet in reality; prefer hard signals over hunches

### Delta Update — minimal shape

```json
{
  "new_bullets": [
    {
      "id": "bullet-2024-10-25-042",
      "title": "string",
      "content": "string",
      "tags": ["string"],
      "evidence": [],
      "helpful_count": 0,
      "harmful_count": 0,
      "links": []
    }
  ],
  "edits": [
    {
      "id": "bullet-existing-id",
      "set": {
        "title": "updated title (optional)",
        "content": "updated content (optional)",
        "tags": ["updated", "tags"]
      }
    }
  ],
  "merges": [
    {
      "keep_id": "bullet-123",
      "merge_ids": ["bullet-456", "bullet-789"],
      "rationale": "why these are true duplicates or redundant"
    }
  ],
  "deprecations": [
    {
      "id": "bullet-obsolete-id",
      "reason": "why this no longer applies (e.g., API changed, pattern refuted)"
    }
  ],
  "counters": [
    {
      "id": "bullet-helpful-id",
      "helpful_delta": 1,
      "harmful_delta": 0
    }
  ]
}
```

> **The runtime/orchestrator** merges deltas deterministically and updates timestamps/counters.

### Modes (for agents that use the ACE skill)

- **Generator** – solves the task with current bullets; outputs strict JSON with `final_answer`, `used_bullet_ids`, `observations`, and calibrated `answer_confidence`.
- **Reflector** – inspects generator output (+ optional ground truth) to propose **proposed_deltas** and mark bullets helpful/harmful.
- **Curator** – normalizes and deduplicates: outputs a **clean_delta** ready for merge. Prefer merges over deletions; keep rare-but-critical edge cases.

### Grow-and-Refine Policy

- **Default:** grow steadily with new bullets when new patterns/heuristics emerge.
- **Refine when:**
  - (a) window pressure is high (context budget strained)
  - (b) redundancy is evident (multiple bullets address same narrow pattern)
  - (c) rules are proven dead (evidence shows obsolescence)
- **Dedup strategy:** semantic similarity + tag overlap + title intent. If in doubt, *keep both* with distinct tags.
- **Archive, don't delete:** deprecated bullets move to an archive file for future reference.

### Retrieval Hints

- Retrieval = semantic match + tags + `helpful_count` + recency weighting.
- Prefer bullets with tags aligned to the task and higher `helpful_count`.
- If a needed tactic is missing, propose it via a **new bullet** in your delta.
- Use negative evidence (`harmful_count > 0`) to downrank or trigger review of problematic bullets.

### Safety & Scope

- Follow platform safety policies (no malicious code, credential harvesting, etc.).
- When feedback is weak (no ground truth/validation), **downgrade edits**:
  - Add `"low_confidence"` bullets instead of high-confidence ones
  - Avoid aggressive merges/deprecations
  - Flag for human review
- Respect scope boundaries: ACE updates context *within* the agent's domain; do not modify system prompts or core policies.

---

## Progressive Disclosure

- **Load this file first**; then read the *mandatory* three files listed above.
- Load additional context **only as needed**:
  - Tools documentation when using specific tools/skills
  - Project-specific notes when working on particular features
  - Domain schemas when dealing with specialized data formats
- When using the ACE skill, its **front matter** (name/description) is cheap; the body and schemas are read **only when invoked**.
- **Lazy loading principle**: Context is abundant, attention is scarce. Read what's necessary for the current task, defer the rest.

---

## Change Control

- Before committing structural changes to memory/projects/tools, propose an ACE **delta** and get user sign-off.
- Use `skills/ace-context-engineering/scripts/validate_delta.py` to sanity-check your delta JSON (optional).
- All context changes should be:
  - **Traceable** (linked to specific tasks, commits, or decisions)
  - **Reversible** (via git history or explicit deprecation/archive)
  - **Reviewable** (clear rationale in delta or commit message)
- High-impact changes (affecting core workflows) require explicit user approval.

---

## Context Evolution Workflow

1. **Task execution** → observe what worked, what didn't
2. **Reflection** → identify gaps, redundancies, or errors in current context
3. **Propose delta** → draft new bullets, edits, merges, or deprecations
4. **Validation** → (optional) run validation script, check for conflicts
5. **Review** → discuss with user if change is non-trivial
6. **Merge** → apply delta, update timestamps and counters
7. **Commit** → version control with clear message

---

## Metadata

- **Version**: 1.0.0
- **Created**: 2025-10-25
- **Last Updated**: 2025-10-25
- **Schema Compatibility**: ACE v1 (bullet + delta minimal shapes)
- **Attribution**: Derived from **"Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models"**
  Q. Zhang et al., 2025, arXiv:2510.04618, **CC BY 4.0**.

---

## Quick Reference

### When to read context

- ✅ Before starting non-trivial tasks
- ✅ When encountering unfamiliar tools or patterns
- ✅ When previous approach failed
- ✅ When user references project-specific conventions

### When to propose deltas

- ✅ After discovering a new useful pattern
- ✅ When existing guidance led to errors
- ✅ When task revealed missing edge cases
- ✅ When redundancy or obsolescence is clear

### When to ask for help

- ⚠️ Context conflicts with task requirements
- ⚠️ Uncertain whether to merge or keep separate bullets
- ⚠️ Proposed change affects core workflows
- ⚠️ Evidence is weak but change seems necessary

---

**End of context.md**
