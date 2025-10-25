# ACE Context Engineering - Complete Examples

This document provides end-to-end walkthroughs of the ACE (Agentic Context Engineering) cycle with concrete examples.

---

## Example 1: Complete ACE Cycle - Adding a Plugin

### Scenario

User asks: "Add a new plugin for syntax highlighting to the marketplace"

### Phase 1: RETRIEVE

**Task analysis:**
- Tags: `domain.plugin_marketplace`, `json`, `validation`, `tool.write`

**Retrieved bullets:**

```json
{
  "retrieved": [
    {
      "id": "bullet-2025-10-25-006",
      "title": "Validate JSON files before committing in plugin marketplace projects",
      "tags": ["domain.plugin_marketplace", "validation", "json", "git.commit"],
      "helpful_count": 5
    },
    {
      "id": "bullet-2025-10-25-002",
      "title": "Use specialized file tools instead of Bash commands",
      "tags": ["tool.bash", "tool.write", "best_practice"],
      "helpful_count": 3
    }
  ],
  "retrieval_rationale": "Task involves creating JSON files in plugin marketplace, so validation and file tool guidance are relevant"
}
```

### Phase 2: GENERATE

**Execution:**

1. Create `plugins/syntax-highlighting/` directory
2. Write `metadata.json` (using Write tool per bullet-2025-10-25-002)
3. Write `README.md`
4. Validate JSON (per bullet-2025-10-25-006)
5. Update `marketplace.json`
6. Validate marketplace.json

**Generator output:**

```json
{
  "final_answer": "Successfully added syntax-highlighting plugin with metadata.json, README.md, and updated marketplace.json. All JSON validated.",
  "used_bullet_ids": [
    "bullet-2025-10-25-002",
    "bullet-2025-10-25-006"
  ],
  "observations": [
    "Write tool worked well for new files",
    "Validation caught missing 'license' field before commit",
    "marketplace.json update required manual edit - no automation"
  ],
  "answer_confidence": "high",
  "missing_guidance": [
    "No bullet about marketplace.json schema or required fields",
    "No guidance about plugin directory naming conventions"
  ]
}
```

### Phase 3: REFLECT

**Reflection analysis:**

- ✅ Both bullets helpful - increment counters
- ❌ Missing guidance on marketplace.json structure
- ❌ Missing guidance on plugin naming conventions
- 💡 Could add bullet about plugin creation workflow

**Proposed deltas:**

```json
{
  "new_bullets": [
    {
      "id": "bullet-2025-10-25-014",
      "title": "Plugin marketplace.json requires specific schema for each plugin entry",
      "content": "When adding plugins to marketplace.json, each entry must include: name (string, unique), version (semver), description (string), author (object with name and optional email/url), tags (array of strings), repository (optional URL), license (string, e.g., 'MIT'). Validate against schemas/plugin.schema.json before committing to prevent CI failures.",
      "tags": ["domain.plugin_marketplace", "json", "schema", "validation"],
      "evidence": [
        {
          "type": "execution",
          "ref": "task-add-syntax-highlighting-plugin",
          "note": "Had to manually check existing entries to understand required fields"
        }
      ],
      "confidence": "high",
      "scope": "project"
    },
    {
      "id": "bullet-2025-10-25-015",
      "title": "Plugin directories should use kebab-case naming",
      "content": "Plugin directory names in the marketplace should use kebab-case (lowercase with hyphens). Example: 'syntax-highlighting', 'code-formatter', 'ai-assistant'. This maintains consistency across the marketplace and avoids case-sensitivity issues across platforms. The directory name should match the plugin's 'name' field in metadata.json.",
      "tags": ["domain.plugin_marketplace", "naming", "convention"],
      "evidence": [
        {
          "type": "execution",
          "ref": "projects/CLAUDE.md",
          "note": "Project conventions specify kebab-case for plugin directories"
        }
      ],
      "confidence": "high",
      "scope": "project"
    }
  ],
  "counters": [
    {
      "id": "bullet-2025-10-25-002",
      "helpful_delta": 1,
      "evidence": {
        "type": "execution",
        "ref": "task-add-syntax-highlighting-plugin",
        "note": "Write tool used successfully for creating plugin files"
      }
    },
    {
      "id": "bullet-2025-10-25-006",
      "helpful_delta": 1,
      "evidence": {
        "type": "validation",
        "ref": "task-add-syntax-highlighting-plugin",
        "note": "JSON validation caught missing license field before commit"
      }
    }
  ]
}
```

### Phase 4: CURATE

**Deduplication check:**

- Search existing bullets for "marketplace.json" → None found
- Search existing bullets for "kebab-case" or "naming" → None found
- Search for similar schema validation → bullet-2025-10-25-006 exists but is generic, new bullet is specific

**Normalized delta:**

```json
{
  "delta_id": "delta-2025-10-25-001",
  "timestamp": "2025-10-25T14:30:00Z",
  "author": "agent",
  "rationale": "Captured plugin marketplace-specific patterns discovered during plugin addition task. Two new bullets address schema requirements and naming conventions that were not previously documented.",
  "task_context": "Adding syntax-highlighting plugin to marketplace",
  "reviewed": false,
  "new_bullets": [
    // ... same as above
  ],
  "counters": [
    // ... same as above
  ]
}
```

**Validation:**

```bash
$ python scripts/validate_delta.py delta-2025-10-25-001.json --playbook playbook.json

=== Delta Validation Results ===

Delta file: delta-2025-10-25-001.json
Playbook: playbook.json

✓ Delta is valid!

Operations: 2 new bullets, 2 counter updates
```

### Phase 5: MERGE

**Apply delta:**

1. Load playbook.json
2. Update counters:
   - bullet-2025-10-25-002: helpful_count 3 → 4
   - bullet-2025-10-25-006: helpful_count 5 → 6
3. Add bullet-2025-10-25-014 and bullet-2025-10-25-015
4. Update metadata:
   - total_bullets: 12 → 14
   - active_bullets: 12 → 14
   - last_curated: 2025-10-25T14:30:00Z
5. Save playbook.json

**Result:**

Playbook now contains 14 active bullets, including domain-specific guidance for plugin marketplace that will help with future plugin additions.

---

## Example 2: Reflection After Failure

### Scenario

Task failed: Git push returned 403 error

### Phase 1-2: RETRIEVE & GENERATE

**Retrieved bullet:**

```json
{
  "id": "bullet-2025-10-25-003",
  "title": "Git push requires branch names starting with 'claude/' to avoid 403 errors",
  "helpful_count": 0,
  "harmful_count": 0
}
```

**Execution:**

Agent attempted: `git push origin feature-branch`
Result: HTTP 403 Forbidden

**Why it failed:**

Agent retrieved the bullet but IGNORED the guidance (didn't follow it).

### Phase 3: REFLECT

**Reflection:**

```json
{
  "proposed_deltas": {
    "counters": [
      {
        "id": "bullet-2025-10-25-003",
        "harmful_delta": 1,
        "evidence": {
          "type": "error_log",
          "ref": "git-push-failure-001",
          "note": "Bullet was retrieved but guidance was not followed, leading to 403 error"
        }
      }
    ],
    "edits": [
      {
        "id": "bullet-2025-10-25-003",
        "set": {
          "title": "CRITICAL: Git push requires branch names starting with 'claude/' to avoid 403",
          "tags": ["tool.bash", "git.push", "error_prevention", "critical", "project", "must_follow"]
        },
        "rationale": "Upgrading criticality to emphasize this is a hard requirement, not optional guidance"
      }
    ]
  },
  "reflection_notes": "Bullet was retrieved but not followed. Need to emphasize criticality and add 'must_follow' tag to ensure it's not skipped."
}
```

**Lesson learned:**

Even when bullets are retrieved, they must be APPLIED. High-stakes rules need clearer signaling (CRITICAL, must_follow tag).

---

## Example 3: Merging Redundant Bullets

### Scenario

Discovered two bullets both addressing JSON validation:

**Bullet A:**

```json
{
  "id": "bullet-2025-10-25-006",
  "title": "Validate JSON files before committing in plugin marketplace projects",
  "content": "Always validate JSON files (metadata.json, marketplace.json) before committing...",
  "tags": ["domain.plugin_marketplace", "validation", "json", "best_practice", "project"],
  "helpful_count": 6,
  "harmful_count": 0
}
```

**Bullet B (hypothetical):**

```json
{
  "id": "bullet-2025-09-15-042",
  "title": "Use jq to validate JSON syntax before git commit",
  "content": "Run 'jq . file.json' before committing JSON files to catch syntax errors...",
  "tags": ["json", "validation", "tool.bash"],
  "helpful_count": 2,
  "harmful_count": 0
}
```

### Analysis

**Similarity:**
- Both about JSON validation before commit
- Overlapping tags: ["json", "validation"]
- Similar intent

**Differences:**
- Bullet A is plugin-marketplace specific
- Bullet B suggests specific tool (jq)
- Different scopes

### Curator Decision

**Option 1: Merge** (if bullets are truly redundant)

```json
{
  "merges": [
    {
      "keep_id": "bullet-2025-10-25-006",
      "merge_ids": ["bullet-2025-09-15-042"],
      "rationale": "Both address JSON validation before commit. Combining to create comprehensive guidance with specific tool recommendation.",
      "merged_content": "Always validate JSON files before committing. Use validation scripts, schemas, or 'jq . file.json' to check syntax. Common issues: trailing commas, unescaped strings, missing brackets. For plugin marketplace, validate against schemas/plugin.schema.json. Validation prevents CI failures and saves time."
    }
  ]
}
```

**Option 2: Keep Both** (if bullets serve different purposes)

No merge. Instead, add link:

```json
{
  "edits": [
    {
      "id": "bullet-2025-10-25-006",
      "set": {
        "links": ["bullet-2025-09-15-042"]
      },
      "rationale": "Link to related bullet about JSON validation tools"
    }
  ]
}
```

**Recommendation:** Keep both if:
- Different scopes (project vs global)
- Different levels of detail (high-level vs tool-specific)
- Different contexts where each applies

Merge if:
- Truly redundant
- One supersedes the other
- Causing confusion

---

## Example 4: Deprecating Obsolete Guidance

### Scenario

Project migrated from npm to pnpm. Old bullet says "use npm install".

**Old bullet:**

```json
{
  "id": "bullet-2024-06-10-018",
  "title": "Run npm install after pulling changes to package.json",
  "content": "When package.json changes are pulled, always run 'npm install' to sync dependencies...",
  "tags": ["tool.bash", "npm", "dependency_management"],
  "helpful_count": 15,
  "harmful_count": 0
}
```

**New bullet:**

```json
{
  "id": "bullet-2025-10-25-016",
  "title": "Run pnpm install after pulling changes to package.json",
  "content": "When package.json changes are pulled, always run 'pnpm install' to sync dependencies. This project uses pnpm for faster installs and better disk efficiency...",
  "tags": ["tool.bash", "pnpm", "dependency_management"],
  "helpful_count": 0,
  "harmful_count": 0
}
```

### Delta

```json
{
  "delta_id": "delta-2025-10-25-002",
  "rationale": "Project migrated from npm to pnpm. Deprecating npm guidance and adding pnpm replacement.",
  "task_context": "Package manager migration",
  "new_bullets": [
    {
      "id": "bullet-2025-10-25-016",
      // ... as above
    }
  ],
  "deprecations": [
    {
      "id": "bullet-2024-06-10-018",
      "reason": "Project migrated from npm to pnpm. npm install no longer used.",
      "replacement_id": "bullet-2025-10-25-016"
    }
  ]
}
```

**After merge:**

- bullet-2024-06-10-018: status = "deprecated", points to replacement
- bullet-2025-10-25-016: status = "active"
- Both preserved in playbook for historical reference

---

## Example 5: Low Confidence Bullet

### Scenario

Agent suspects pattern but lacks strong evidence.

**Observation:**

"It seems like Grep might be faster with --type flag instead of --glob, but I only tried once."

### Proposed Bullet (Low Confidence)

```json
{
  "id": "bullet-2025-10-25-017",
  "title": "Prefer Grep --type over --glob for performance",
  "content": "When searching specific file types, use --type flag (e.g., --type js) instead of --glob (e.g., --glob '*.js'). The --type flag may be more optimized in ripgrep. However, this needs more testing to confirm performance difference.",
  "tags": ["tool.grep", "performance", "low_confidence"],
  "evidence": [
    {
      "type": "low_confidence",
      "ref": "single-observation-2025-10-25",
      "note": "Observed faster result once, but not rigorously tested"
    }
  ],
  "confidence": "low",
  "scope": "global",
  "helpful_count": 0,
  "harmful_count": 0
}
```

**Strategy:**

1. Add bullet with `confidence: "low"` and `low_confidence` tag
2. Use it tentatively in future tasks
3. Track helpful/harmful counts
4. If proven helpful (count > 5), upgrade to `confidence: "medium"`
5. If proven harmful (harmful > helpful), deprecate

**Progressive Validation:**

- Start: confidence=low, helpful=0, harmful=0
- After 10 uses: helpful=7, harmful=1 → upgrade to medium
- After 30 uses: helpful=28, harmful=0 → upgrade to high

---

## Example 6: Counter-Only Delta (Simple Update)

### Scenario

Used several bullets successfully, no new patterns discovered.

### Delta

```json
{
  "delta_id": "delta-2025-10-25-003",
  "timestamp": "2025-10-25T16:00:00Z",
  "rationale": "Standard task execution with existing guidance. Updating effectiveness counters.",
  "task_context": "Fixed bug in validation logic",
  "counters": [
    {"id": "bullet-2025-10-25-001", "helpful_delta": 1},
    {"id": "bullet-2025-10-25-012", "helpful_delta": 1},
    {"id": "bullet-2025-10-25-007", "helpful_delta": 1}
  ]
}
```

**When to use counter-only deltas:**

✅ Task completed successfully with existing guidance
✅ No new patterns emerged
✅ Want to track bullet effectiveness
✅ Simple, low-risk update

---

## Example 7: Edit to Improve Existing Bullet

### Scenario

Bullet exists but is vague. After using it, agent can make it more specific.

**Before:**

```json
{
  "id": "bullet-2025-10-25-010",
  "title": "Grep requires exact escaping of literal braces",
  "content": "When searching for braces, you need to escape them.",
  "tags": ["tool.grep", "regex"]
}
```

**After using it:** Agent realizes it's specifically about ripgrep vs grep, and needs examples.

### Delta

```json
{
  "edits": [
    {
      "id": "bullet-2025-10-25-010",
      "set": {
        "title": "Grep requires exact escaping of literal braces for Go/Rust interface syntax",
        "content": "When searching for code with literal braces (e.g., Go's 'interface{}', Rust's 'struct {}'), you must escape the braces in Grep patterns because it uses ripgrep (not grep) syntax. Use 'interface\\{\\}' to find 'interface{}'. Also note: Grep matches single lines by default; use multiline: true for patterns that span lines. Common error: forgetting to escape causes pattern to match nothing.",
        "tags": ["tool.grep", "regex", "edge_case", "go", "rust"]
      },
      "rationale": "Expanded with specific examples (Go, Rust), clarified ripgrep vs grep difference, added multiline note, and included common error. Makes bullet much more actionable."
    }
  ]
}
```

**Result:** Bullet is more specific, has examples, and is easier to apply correctly.

---

## Common Patterns Summary

### When to Add New Bullets

✅ Discovered edge case not covered
✅ Found tool usage recipe that worked well
✅ Identified common error pattern
✅ Learned domain-specific convention
✅ Found gap during task execution

### When to Update Counters

✅ After every task where bullets were used
✅ When bullet helped avoid error (helpful+1)
✅ When bullet led to wrong approach (harmful+1)
✅ Batch counter updates for efficiency

### When to Edit Bullets

✅ Vague → Specific (add examples, clarify)
✅ Incomplete → Complete (add missing context)
✅ Wrong → Corrected (fix errors)
✅ Outdated → Current (update for changes)

### When to Merge Bullets

✅ True duplicates (same intent, same tags)
✅ One bullet supersedes another
✅ Combining creates clearer guidance
⚠️ Be conservative - prefer keeping both if uncertain

### When to Deprecate Bullets

✅ Proven wrong (harmful >> helpful)
✅ Technology/API changed
✅ Pattern no longer applies
✅ Superseded by better guidance

---

## Best Practices Learned

1. **Start with retrieval** - Always query bullets before execution
2. **Track usage** - Note which bullets you actually use
3. **Be specific** - Generic advice is low-value
4. **Include evidence** - Ground bullets in execution reality
5. **Tag well** - Good tags enable good retrieval
6. **Link related bullets** - Build knowledge graph
7. **Progressive confidence** - Start low, upgrade with evidence
8. **Preserve history** - Deprecate, don't delete
9. **Validate before merge** - Catch errors early
10. **Review high-impact changes** - Get user sign-off

---

## Anti-Patterns to Avoid

❌ Adding bullets without evidence ("I think maybe...")
❌ Merging bullets that serve different contexts
❌ Deleting deprecated bullets (archive instead)
❌ Generic, vague content ("be careful", "think about...")
❌ Not tracking which bullets were used
❌ Skipping validation step
❌ Monolithic rewrites instead of incremental deltas
❌ Not linking related bullets
❌ Ignoring harmful_count signals
❌ Not updating counters regularly

---

**End of examples**
