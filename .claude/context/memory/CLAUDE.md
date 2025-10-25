# Memory Context

## Purpose

This file defines the memory model, retrieval policies, and counter management for the Claude Code agent working on this project.

---

## Memory Model

### Short-term Memory (Conversation Context)

- **Scope**: Current conversation session
- **Retention**: Active throughout session
- **Contents**:
  - User requests and clarifications
  - Tool invocations and results
  - Task progress and state
  - Temporary decisions and reasoning

### Long-term Memory (Persistent Context)

- **Scope**: Cross-session, project-wide
- **Retention**: Stored in `.claude/context/` files, version-controlled
- **Contents**:
  - Project structure and conventions
  - Common patterns and anti-patterns
  - Tool usage policies and recipes
  - Learned heuristics (via ACE bullets)

---

## Retrieval Policy

### When to retrieve from memory

1. **Task initiation**: Read mandatory context files (context.md, projects/CLAUDE.md, tools/CLAUDE.md)
2. **Uncertainty**: When facing ambiguity or unfamiliar patterns
3. **Failure recovery**: When previous approach didn't work
4. **Domain switch**: When moving to different area of codebase or different task type

### Retrieval priorities

1. **Task-specific context**: Highest priority (project notes, domain schemas)
2. **Tool guidance**: When using specific tools or skills
3. **Pattern library**: When implementing features or fixing bugs
4. **Historical lessons**: When similar tasks were performed before

### Progressive loading

- Start with high-level context (this file, context.md)
- Load specific context as needed (tools, projects, domains)
- Avoid loading entire context tree upfront (attention budget)

---

## Counter Management

### Bullet effectiveness counters

Each ACE bullet tracks:

- `helpful_count`: Incremented when bullet contributed to correct solution
- `harmful_count`: Incremented when bullet led to errors or inefficiency
- `last_updated`: Timestamp of last modification

### When to update counters

- ✅ After task completion: mark bullets that helped as helpful
- ✅ After errors: mark bullets that misled as harmful
- ✅ During reflection: assess which guidance was valuable
- ⚠️ Be conservative: only update when causation is clear

### Counter decay

- Older bullets with low helpful_count may be candidates for deprecation
- Recent bullets need more evidence before high confidence
- High harmful_count triggers review or deprecation proposal

---

## Memory Hygiene

### Keep memory current

- Remove or deprecate obsolete guidance after major refactors
- Update tool usage notes when APIs change
- Refresh project context when architecture evolves

### Avoid memory bloat

- Merge redundant bullets (via ACE delta merges)
- Archive rarely-used but historically important bullets
- Prefer links to external docs over embedding full specifications

### Version control

- All memory changes are version-controlled via git
- Significant changes include clear commit messages
- Breaking changes to memory structure require user approval

---

## Quick Checklist

Before starting non-trivial work:

- [ ] Read `.claude/context/context.md` (system overview)
- [ ] Read `.claude/context/projects/CLAUDE.md` (project navigation)
- [ ] Read `.claude/context/tools/CLAUDE.md` (tool policies)
- [ ] Load task-specific context as needed
- [ ] Review relevant bullets from ACE playbook (if established)

After completing work:

- [ ] Reflect on which context was helpful or missing
- [ ] Propose ACE delta if new patterns emerged
- [ ] Update counters for bullets that were used
- [ ] Document any project-specific learnings

---

## Future Enhancements

This memory system can be extended with:

- **Semantic search** over bullet library (embedding-based retrieval)
- **Automated counter updates** based on test success/failure
- **Conflict detection** between bullets
- **Importance scoring** combining recency, counters, and task relevance
- **Memory compression** for large playbooks

---

**Last Updated**: 2025-10-25
